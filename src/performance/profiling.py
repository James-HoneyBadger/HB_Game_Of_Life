"""
Profiling tools for analyzing memory usage and execution performance.

This module provides utilities for profiling memory consumption and
identifying performance bottlenecks in simulations.
"""

import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MemorySnapshot:
    """A snapshot of memory usage at a point in time.

    Attributes:
        timestamp: When the snapshot was taken
        current_mb: Current memory usage in MB
        peak_mb: Peak memory usage in MB
        label: Optional label for the snapshot
    """

    timestamp: float
    current_mb: float
    peak_mb: float
    label: str = ""

    def __str__(self) -> str:
        """Format snapshot as a string."""
        label_str = f" ({self.label})" if self.label else ""
        return (
            f"Memory Snapshot{label_str}: "
            f"Current: {self.current_mb:.2f}MB, "
            f"Peak: {self.peak_mb:.2f}MB"
        )


class MemoryProfiler:
    """Profile memory usage during simulation.

    This profiler tracks memory allocations and can identify
    memory-intensive operations.
    """

    def __init__(self):
        self.snapshots: List[MemorySnapshot] = []
        self.is_running = False
        self._start_time: Optional[float] = None

    def start(self) -> None:
        """Start memory profiling."""
        if self.is_running:
            return

        tracemalloc.start()
        self.snapshots.clear()
        self.is_running = True
        self._start_time = time.time()
        self.take_snapshot("start")

    def stop(self) -> None:
        """Stop memory profiling."""
        if not self.is_running:
            return

        self.take_snapshot("stop")
        tracemalloc.stop()
        self.is_running = False

    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """Take a snapshot of current memory usage.

        Args:
            label: Optional label for the snapshot

        Returns:
            MemorySnapshot object
        """
        if not self.is_running:
            raise RuntimeError("Profiler is not running. Call start() first.")

        current, peak = tracemalloc.get_traced_memory()
        snapshot = MemorySnapshot(
            timestamp=time.time() - (self._start_time or 0),
            current_mb=current / (1024 * 1024),
            peak_mb=peak / (1024 * 1024),
            label=label,
        )
        self.snapshots.append(snapshot)
        return snapshot

    def get_memory_increase(self) -> float:
        """Get the memory increase from start to current.

        Returns:
            Memory increase in MB
        """
        if len(self.snapshots) < 2:
            return 0.0

        return self.snapshots[-1].current_mb - self.snapshots[0].current_mb

    def get_peak_memory(self) -> float:
        """Get the peak memory usage.

        Returns:
            Peak memory in MB
        """
        if not self.snapshots:
            return 0.0

        return max(s.peak_mb for s in self.snapshots)

    def get_report(self) -> str:
        """Generate a memory profiling report.

        Returns:
            Formatted report string
        """
        if not self.snapshots:
            return "No snapshots available. Start profiling first."

        lines = [
            "\n" + "=" * 70,
            "Memory Profiling Report",
            "=" * 70 + "\n",
            f"Total Snapshots: {len(self.snapshots)}",
            f"Duration: {self.snapshots[-1].timestamp:.2f}s\n",
            f"{'Label':<20} {'Time':<12} {'Current':<12} {'Peak':<12}",
            "-" * 70,
        ]

        for snapshot in self.snapshots:
            lines.append(
                f"{snapshot.label:<20} "
                f"{snapshot.timestamp:>8.2f}s    "
                f"{snapshot.current_mb:>8.2f}MB   "
                f"{snapshot.peak_mb:>8.2f}MB"
            )

        lines.append("-" * 70)
        lines.append(f"Memory Increase: {self.get_memory_increase():.2f}MB")
        lines.append(f"Peak Memory: {self.get_peak_memory():.2f}MB")
        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    @contextmanager
    def profile_section(self, label: str):
        """Context manager for profiling a section of code.

        Args:
            label: Label for the profiled section

        Yields:
            None

        Example:
            >>> profiler = MemoryProfiler()
            >>> profiler.start()
            >>> with profiler.profile_section("simulation"):
            ...     # Run simulation
            ...     pass
            >>> profiler.stop()
        """
        self.take_snapshot(f"{label}_start")
        try:
            yield
        finally:
            self.take_snapshot(f"{label}_end")


@dataclass
class ProfileResult:
    """Result from a performance profile.

    Attributes:
        name: Name of the profiled operation
        duration: Total duration in seconds
        call_count: Number of times the function was called
        memory_used: Memory used in MB
        metadata: Additional metadata
    """

    name: str
    duration: float
    call_count: int
    memory_used: float
    metadata: Dict[str, Any]

    def __str__(self) -> str:
        """Format profile result as a string."""
        return (
            f"Profile: {self.name}\n"
            f"  Duration: {self.duration * 1000:.2f}ms\n"
            f"  Calls: {self.call_count}\n"
            f"  Memory: {self.memory_used:.2f}MB\n"
            f"  Avg Time/Call: "
            f"{(self.duration / self.call_count) * 1000:.2f}ms"
        )


class PerformanceProfiler:
    """Profile execution performance of specific operations.

    This profiler measures execution time and can track
    function call counts and timing patterns.
    """

    def __init__(self):
        self.profiles: Dict[str, ProfileResult] = {}
        self._timers: Dict[str, float] = {}
        self._counts: Dict[str, int] = {}
        self._memory_start: Dict[str, float] = {}

    @contextmanager
    def profile(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for profiling a block of code.

        Args:
            name: Name for this profile
            metadata: Optional metadata to store

        Yields:
            None

        Example:
            >>> profiler = PerformanceProfiler()
            >>> with profiler.profile("grid_update"):
            ...     # Update grid
            ...     pass
        """
        # Start timing
        start_time = time.perf_counter()

        # Track memory if tracemalloc is active
        memory_start = 0.0
        if tracemalloc.is_tracing():
            memory_start, _ = tracemalloc.get_traced_memory()

        try:
            yield
        finally:
            # End timing
            end_time = time.perf_counter()
            duration = end_time - start_time

            # Calculate memory usage
            memory_used = 0.0
            if tracemalloc.is_tracing():
                memory_end, _ = tracemalloc.get_traced_memory()
                memory_used = (memory_end - memory_start) / (1024 * 1024)

            # Update or create profile
            if name in self.profiles:
                profile = self.profiles[name]
                profile.duration += duration
                profile.call_count += 1
                profile.memory_used += memory_used
            else:
                self.profiles[name] = ProfileResult(
                    name=name,
                    duration=duration,
                    call_count=1,
                    memory_used=memory_used,
                    metadata=metadata or {},
                )

    def get_profile(self, name: str) -> Optional[ProfileResult]:
        """Get a specific profile result.

        Args:
            name: Name of the profile

        Returns:
            ProfileResult or None if not found
        """
        return self.profiles.get(name)

    def get_all_profiles(self) -> List[ProfileResult]:
        """Get all profile results.

        Returns:
            List of ProfileResult objects
        """
        return list(self.profiles.values())

    def get_report(self) -> str:
        """Generate a performance profiling report.

        Returns:
            Formatted report string
        """
        if not self.profiles:
            return "No profiles available. Profile some operations first."

        lines = [
            "\n" + "=" * 70,
            "Performance Profiling Report",
            "=" * 70 + "\n",
            f"Total Profiles: {len(self.profiles)}\n",
            f"{'Name':<25} {'Calls':<10} {'Total Time':<15} {'Avg Time':<15}",
            "-" * 70,
        ]

        # Sort by total duration
        sorted_profiles = sorted(
            self.profiles.values(), key=lambda p: p.duration, reverse=True
        )

        total_time = sum(p.duration for p in sorted_profiles)

        for profile in sorted_profiles:
            avg_time = profile.duration / profile.call_count
            percentage = (
                (profile.duration / total_time * 100) if total_time > 0 else 0
            )

            lines.append(
                f"{profile.name:<25} "
                f"{profile.call_count:<10} "
                f"{profile.duration * 1000:>10.2f}ms    "
                f"{avg_time * 1000:>10.2f}ms ({percentage:>5.1f}%)"
            )

        lines.append("-" * 70)
        lines.append(f"Total Time: {total_time * 1000:.2f}ms")
        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all profiling data."""
        self.profiles.clear()
        self._timers.clear()
        self._counts.clear()
        self._memory_start.clear()

    def measure_function(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        iterations: int = 1,
        **kwargs,
    ) -> ProfileResult:
        """Measure the performance of a function.

        Args:
            func: Function to measure
            *args: Arguments to pass to the function
            name: Optional name for the profile (defaults to function name)
            iterations: Number of times to run the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            ProfileResult with timing information
        """
        profile_name = name or func.__name__

        for _ in range(iterations):
            with self.profile(profile_name):
                func(*args, **kwargs)

        return self.profiles[profile_name]
