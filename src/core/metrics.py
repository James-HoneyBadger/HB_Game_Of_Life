"""Shared simulation metric calculations."""

from __future__ import annotations

import numpy as np


def calculate_transition_metrics(
    previous_grid: np.ndarray,
    current_grid: np.ndarray,
    generation: int,
    state_count: int,
) -> dict:
    """Calculate stable metrics for one simulation transition."""
    if previous_grid.shape != current_grid.shape:
        raise ValueError("Previous and current grids must have the same shape")
    if current_grid.ndim != 2:
        raise ValueError("Simulation grids must be two-dimensional")

    previous_alive = previous_grid != 0
    current_alive = current_grid != 0
    population = int(np.count_nonzero(current_grid))
    return {
        "generation": generation,
        "population": population,
        "density": float(population / current_grid.size),
        "births": int(np.count_nonzero(~previous_alive & current_alive)),
        "deaths": int(np.count_nonzero(previous_alive & ~current_alive)),
        "state_counts": {
            str(state): int(np.count_nonzero(current_grid == state))
            for state in range(state_count)
        },
    }
