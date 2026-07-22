"""
Benchmarking tools for measuring automaton and rendering performance.

This module provides comprehensive benchmarking capabilities for measuring
the performance of different aspects of LifeGrid simulations.
"""

import json
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np


@dataclass
class BenchmarkResult:
    """Results from a benchmark run.

    Attributes:
        name: Name of the benchmark
        iterations: Number of iterations run
        total_time: Total execution time in seconds
        mean_time: Mean time per iteration in seconds
        median_time: Median time per iteration in seconds
        std_dev: Standard deviation of iteration times
        min_time: Minimum iteration time
        max_time: Maximum iteration time
        throughput: Iterations per second
        metadata: Additional metadata about the benchmark
    """

    # pylint: disable=too-many-instance-attributes

    name: str
    iterations: int
    total_time: float
    mean_time: float
    median_time: float
    std_dev: float
    min_time: float
    max_time: float
    throughput: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format benchmark results as a string."""
        return (
            f"Benchmark: {self.name}\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total Time: {self.total_time:.4f}s\n"
            f"  Mean Time: {self.mean_time * 1000:.2f}ms\n"
            f"  Median Time: {self.median_time * 1000:.2f}ms\n"
            f"  Std Dev: {self.std_dev * 1000:.2f}ms\n"
            f"  Min Time: {self.min_time * 1000:.2f}ms\n"
            f"  Max Time: {self.max_time * 1000:.2f}ms\n"
            f"  Throughput: {self.throughput:.2f} iter/s"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "mean_time": self.mean_time,
            "median_time": self.median_time,
            "std_dev": self.std_dev,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "throughput": self.throughput,
            "metadata": self.metadata,
        }


class Benchmark:
    # pylint: disable=too-few-public-methods
    """A single benchmark test.

    Args:
        name: Name of the benchmark
        function: Function to benchmark
        iterations: Number of iterations to run
        warmup_iterations: Number of warmup iterations before timing
        metadata: Additional metadata about the benchmark
    """

    def __init__(
        self,
        name: str,
        function: Callable[[], None],
        iterations: int = 100,
        warmup_iterations: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        self.name = name
        self.function = function
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.metadata = metadata or {}

    def run(self) -> BenchmarkResult:
        """Run the benchmark and return results.

        Returns:
            BenchmarkResult containing performance metrics
        """
        # Warmup phase
        for _ in range(self.warmup_iterations):
            self.function()

        # Benchmark phase
        times: List[float] = []
        start_total = time.perf_counter()

        for _ in range(self.iterations):
            start = time.perf_counter()
            self.function()
            end = time.perf_counter()
            times.append(end - start)

        end_total = time.perf_counter()
        total_time = end_total - start_total

        # Calculate statistics
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / total_time if total_time > 0 else 0.0

        return BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            total_time=total_time,
            mean_time=mean_time,
            median_time=median_time,
            std_dev=std_dev,
            min_time=min_time,
            max_time=max_time,
            throughput=throughput,
            metadata=self.metadata,
        )


class BenchmarkSuite:
    """A collection of benchmarks to run together.

    This class allows organizing and running multiple related benchmarks,
    comparing their results, and generating reports.
    """

    def __init__(self, name: str = "Benchmark Suite"):
        self.name = name
        self.benchmarks: List[Benchmark] = []
        self.results: List[BenchmarkResult] = []

    def add_benchmark(self, benchmark: Benchmark) -> None:
        """Add a benchmark to the suite.

        Args:
            benchmark: Benchmark to add
        """
        self.benchmarks.append(benchmark)

    def add_automaton_benchmark(
        self,
        name: str,
        automaton: Any,
        grid_size: tuple[int, int],
        steps: int = 100,
        iterations: int = 10,
    ) -> None:
        """Add a benchmark for an automaton.

        Args:
            name: Name of the benchmark
            automaton: Automaton to benchmark
            grid_size: Size of the grid (width, height)
            steps: Number of simulation steps per iteration
            iterations: Number of benchmark iterations
        """
        # pylint: disable=too-many-arguments, too-many-positional-arguments

        def benchmark_func():
            for _ in range(steps):
                automaton.step()

        metadata = {
            "automaton": type(automaton).__name__,
            "grid_size": grid_size,
            "steps": steps,
            "total_cells": grid_size[0] * grid_size[1],
        }

        benchmark = Benchmark(
            name=name,
            function=benchmark_func,
            iterations=iterations,
            metadata=metadata,
        )
        self.add_benchmark(benchmark)

    def add_simulator_benchmark(
        self,
        name: str,
        simulator: Any,
        steps: int = 100,
        iterations: int = 10,
    ) -> None:
        """Add a benchmark for a simulator.

        Args:
            name: Name of the benchmark
            simulator: Simulator to benchmark
            steps: Number of simulation steps per iteration
            iterations: Number of benchmark iterations
        """

        def benchmark_func():
            for _ in range(steps):
                simulator.step()

        grid_shape = getattr(simulator, "grid", np.array([[]])).shape

        metadata = {
            "automaton": (
                type(simulator.automaton).__name__
                if hasattr(simulator, "automaton")
                else "Unknown"
            ),
            "grid_size": grid_shape,
            "steps": steps,
            "total_cells": np.prod(grid_shape) if grid_shape else 0,
        }

        benchmark = Benchmark(
            name=name,
            function=benchmark_func,
            iterations=iterations,
            metadata=metadata,
        )
        self.add_benchmark(benchmark)

    def run_all(self, verbose: bool = True) -> List[BenchmarkResult]:
        """Run all benchmarks in the suite.

        Args:
            verbose: Whether to print progress and results

        Returns:
            List of BenchmarkResult objects
        """
        self.results.clear()

        if verbose:
            print(f"\n{'=' * 70}")
            print(f"Running {self.name}")
            print(f"{'=' * 70}\n")

        for i, benchmark in enumerate(self.benchmarks, 1):
            if verbose:
                print(
                    (
                        f"[{i}/{len(self.benchmarks)}] Running: "
                        f"{benchmark.name}..."
                    )
                )

            result = benchmark.run()
            self.results.append(result)

            if verbose:
                print(
                    f"  Mean: {result.mean_time * 1000:.2f}ms, "
                    f"Throughput: {result.throughput:.2f} iter/s\n"
                )

        if verbose:
            print(f"{'=' * 70}")
            print("Benchmark Suite Complete")
            print(f"{'=' * 70}\n")

        return self.results

    def get_summary(self) -> str:
        """Generate a summary report of all benchmark results.

        Returns:
            Formatted summary string
        """
        if not self.results:
            return "No benchmark results available. Run benchmarks first."

        lines = [
            f"\n{'=' * 70}",
            f"{self.name} - Summary",
            f"{'=' * 70}\n",
            f"Total Benchmarks: {len(self.results)}\n",
        ]

        # Sort by mean time for easy comparison
        sorted_results = sorted(self.results, key=lambda r: r.mean_time)

        lines.append(f"{'Benchmark':<30} {'Mean Time':<15} {'Throughput':<15}")
        lines.append(f"{'-' * 70}")

        for result in sorted_results:
            lines.append(
                f"{result.name:<30} "
                f"{result.mean_time * 1000:>10.2f}ms    "
                f"{result.throughput:>10.2f} iter/s"
            )

        # Find fastest and slowest
        fastest = sorted_results[0]
        slowest = sorted_results[-1]

        lines.append(f"\n{'-' * 70}")
        lines.append(
            f"Fastest: {fastest.name}"
            f" ({fastest.mean_time * 1000:.2f}ms)"
        )
        lines.append(
            f"Slowest: {slowest.name}"
            f" ({slowest.mean_time * 1000:.2f}ms)"
        )

        if len(sorted_results) > 1:
            speedup = slowest.mean_time / fastest.mean_time
            lines.append(f"Speedup: {speedup:.2f}x")

        lines.append(f"{'=' * 70}\n")

        return "\n".join(lines)

    def compare_results(
        self, metric: str = "mean_time", ascending: bool = True
    ) -> List[BenchmarkResult]:
        """Compare benchmark results by a specific metric.

        Args:
            metric: Metric to compare by (mean_time, throughput, etc.)
            ascending: Sort in ascending order

        Returns:
            Sorted list of benchmark results
        """
        return sorted(
            self.results,
            key=lambda r: getattr(r, metric),
            reverse=not ascending,
        )

    def export_results(self, filepath: str) -> None:
        """Export benchmark results to a JSON file.

        Args:
            filepath: Path to save the results
        """
        data = {
            "suite_name": self.name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "benchmarks": [r.to_dict() for r in self.results],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
