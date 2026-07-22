"""
Optimization utilities for improving simulation performance.

This module provides tools for parallel processing and viewport culling
to improve the performance of large simulations.
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Callable, Optional, Tuple

import numpy as np


class ParallelProcessor:
    """Parallel processing for grid updates.

    This class enables parallel computation of cellular automaton updates
    for large grids by dividing the work across multiple CPU cores.

    Args:
        num_workers: Number of worker processes (default: CPU count)
        use_processes: Use processes instead of threads (better for CPU-bound)
    """

    def __init__(
        self, num_workers: Optional[int] = None, use_processes: bool = True
    ):
        self.num_workers = num_workers or mp.cpu_count()
        self.use_processes = use_processes
        self._executor = None

    def __enter__(self):
        """Enter context manager."""
        if self.use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def _split_chunks(
        self, grid: np.ndarray, height: int, chunk_size: int
    ) -> tuple[list[np.ndarray], list[tuple[int, int, int]]]:
        """Split grid into chunks with overlap."""
        chunks = []
        chunk_indices = []

        for i in range(0, height, chunk_size):
            end = min(i + chunk_size, height)
            # Include one row of overlap for boundary calculations
            start_overlap = max(0, i - 1)
            end_overlap = min(height, end + 1)

            chunk = grid[start_overlap:end_overlap].copy()
            chunks.append(chunk)
            chunk_indices.append((i, end, start_overlap))

        return chunks, chunk_indices

    def parallel_grid_update(
        self,
        grid: np.ndarray,
        update_func: Callable[[np.ndarray], np.ndarray],
        chunk_size: Optional[int] = None,
    ) -> np.ndarray:
        """Update grid in parallel by splitting into chunks.

        Args:
            grid: The grid to update
            update_func: Function that takes a grid and returns updated grid
            chunk_size: Size of chunks (default: grid_height / num_workers)

        Returns:
            Updated grid
        """
        height, _ = grid.shape[:2]

        if chunk_size is None:
            chunk_size = max(1, height // self.num_workers)

        # Split grid into horizontal chunks
        chunks, chunk_indices = self._split_chunks(grid, height, chunk_size)

        # Process chunks in parallel
        if not self._executor:
            # If not using context manager, create temporary executor
            executor_class = (
                ProcessPoolExecutor
                if self.use_processes
                else ThreadPoolExecutor
            )
            with executor_class(max_workers=self.num_workers) as executor:
                results = list(executor.map(update_func, chunks))
        else:
            results = list(self._executor.map(update_func, chunks))

        # Combine results
        output = np.zeros_like(grid)

        for (start, end, start_overlap), result in zip(chunk_indices, results):
            # Extract the non-overlap portion
            overlap_offset = start - start_overlap
            result_slice = result[
                overlap_offset:overlap_offset + (end - start)
            ]
            output[start:end] = result_slice

        return output

    @staticmethod
    def should_use_parallel(
        grid_size: Tuple[int, int], threshold: int = 500
    ) -> bool:
        """Determine if parallel processing would be beneficial.

        Args:
            grid_size: Size of the grid (width, height)
            threshold: Minimum grid dimension to use parallel processing

        Returns:
            True if parallel processing is recommended
        """
        width, height = grid_size
        return max(width, height) >= threshold


class ViewportCuller:
    """Optimize rendering by only processing visible cells.

    This class helps improve performance when rendering large grids by
    only computing updates for cells within the viewport.

    Args:
        grid_shape: Shape of the full grid (height, width)
    """

    def __init__(self, grid_shape: Tuple[int, int]):
        self.grid_height, self.grid_width = grid_shape
        self._viewport: Optional[Tuple[int, int, int, int]] = None
        self._viewport_buffer = 0

    def set_viewport(
        self, x: int, y: int, width: int, height: int, buffer: int = 10
    ) -> None:
        """Set the viewport area.

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Width of viewport
            height: Height of viewport
            buffer: Additional buffer around viewport (in cells)
        """
        self._viewport = (x, y, width, height)
        self._viewport_buffer = buffer

    def get_visible_region(self) -> Tuple[int, int, int, int]:
        """Get the visible region with buffer.

        Returns:
            Tuple of (x_start, y_start, x_end, y_end)
        """
        if self._viewport is None:
            return (0, 0, self.grid_width, self.grid_height)

        x, y, width, height = self._viewport
        buffer = self._viewport_buffer

        # Add buffer and clamp to grid bounds
        x_start = max(0, x - buffer)
        y_start = max(0, y - buffer)
        x_end = min(self.grid_width, x + width + buffer)
        y_end = min(self.grid_height, y + height + buffer)

        return (x_start, y_start, x_end, y_end)

    def extract_visible_grid(
        self, grid: np.ndarray
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Extract only the visible portion of the grid.

        Args:
            grid: The full grid

        Returns:
            Tuple of (visible_grid, offset) where offset is (x, y)
        """
        x_start, y_start, x_end, y_end = self.get_visible_region()
        visible_grid = grid[y_start:y_end, x_start:x_end].copy()
        return visible_grid, (x_start, y_start)

    def merge_visible_grid(
        self,
        full_grid: np.ndarray,
        visible_grid: np.ndarray,
        offset: Tuple[int, int],
    ) -> np.ndarray:
        """Merge the updated visible grid back into the full grid.

        Args:
            full_grid: The full grid
            visible_grid: The updated visible portion
            offset: Offset of the visible grid (x, y)

        Returns:
            Updated full grid
        """
        x_offset, y_offset = offset
        height, width = visible_grid.shape[:2]

        result = full_grid.copy()
        result[y_offset:y_offset + height, x_offset:x_offset + width] = (
            visible_grid
        )

        return result

    def is_viewport_set(self) -> bool:
        """Check if viewport has been configured.

        Returns:
            True if viewport is set
        """
        return self._viewport is not None

    def calculate_savings(self) -> float:
        """Calculate the percentage of grid that is culled.

        Returns:
            Percentage of grid not processed (0-100)
        """
        if self._viewport is None:
            return 0.0

        x_start, y_start, x_end, y_end = self.get_visible_region()
        visible_area = (x_end - x_start) * (y_end - y_start)
        total_area = self.grid_width * self.grid_height

        if total_area == 0:
            return 0.0

        culled_percentage = (1.0 - visible_area / total_area) * 100
        return max(0.0, culled_percentage)

    def reset_viewport(self) -> None:
        """Reset the viewport to show the entire grid."""
        self._viewport = None
        self._viewport_buffer = 0


def optimize_grid_dtype(grid: np.ndarray, num_states: int) -> np.ndarray:
    """Optimize grid data type based on number of states.

    Args:
        grid: The grid to optimize
        num_states: Number of possible states

    Returns:
        Grid with optimized dtype
    """
    dtype: Any
    if num_states <= 2:
        dtype = np.bool_
    elif num_states <= 256:
        dtype = np.uint8
    elif num_states <= 65536:
        dtype = np.uint16
    else:
        dtype = np.uint32

    return grid.astype(dtype, copy=False)


def calculate_optimal_chunk_size(
    grid_size: Tuple[int, int], num_workers: int, min_chunk_size: int = 50
) -> int:
    """Calculate optimal chunk size for parallel processing.

    Args:
        grid_size: Size of the grid (width, height)
        num_workers: Number of worker processes
        min_chunk_size: Minimum chunk size

    Returns:
        Optimal chunk size
    """
    height = grid_size[1]
    chunk_size = max(min_chunk_size, height // (num_workers * 2))
    return chunk_size


def estimate_memory_usage(
    grid_shape: Tuple[int, int], dtype: np.dtype
) -> float:
    """Estimate memory usage for a grid.

    Args:
        grid_shape: Shape of the grid
        dtype: Data type of the grid

    Returns:
        Estimated memory usage in MB
    """
    height, width = grid_shape
    bytes_per_cell = np.dtype(dtype).itemsize
    total_bytes = height * width * bytes_per_cell
    return total_bytes / (1024 * 1024)
