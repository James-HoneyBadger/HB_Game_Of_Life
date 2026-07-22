"""
Performance optimization and profiling tools for LifeGrid.

This module provides utilities for measuring, analyzing, and optimizing
the performance of cellular automaton simulations.
"""

from .benchmarking import Benchmark, BenchmarkResult, BenchmarkSuite
from .optimization import ParallelProcessor, ViewportCuller
from .profiling import MemoryProfiler, PerformanceProfiler

__all__ = [
    "Benchmark",
    "BenchmarkSuite",
    "BenchmarkResult",
    "MemoryProfiler",
    "PerformanceProfiler",
    "ParallelProcessor",
    "ViewportCuller",
]
