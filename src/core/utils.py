"""Utility functions for LifeGrid core operations."""

import numpy as np


def place_pattern_centered(
    target_grid: np.ndarray,
    pattern: np.ndarray,
) -> None:
    """Place a pattern on the target grid, centered.

    Args:
        target_grid: The grid to place pattern on (modified in-place)
        pattern: The pattern grid to place
    """
    h, w = target_grid.shape
    ph, pw = pattern.shape

    y_off = (h - ph) // 2
    x_off = (w - pw) // 2

    # Calculate bounds
    y_start = max(0, y_off)
    y_end = min(h, y_off + ph)
    x_start = max(0, x_off)
    x_end = min(w, x_off + pw)

    # Source bounds
    py_start = max(0, -y_off)
    py_end = py_start + (y_end - y_start)
    px_start = max(0, -x_off)
    px_end = px_start + (x_end - x_start)

    if y_end > y_start and x_end > x_start:
        target_grid[y_start:y_end, x_start:x_end] = pattern[
            py_start:py_end, px_start:px_end
        ]
