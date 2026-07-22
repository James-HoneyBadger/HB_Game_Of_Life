"""Cell age tracking and history management.

This module provides capabilities for tracking cell ages, creating
heatmap visualizations, and managing cell histories.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


class CellAgeTracker:
    """Track the age of living cells across generations.

    Maintains a grid where each value represents how many generations
    a cell has been alive continuously.

    Args:
        width: Grid width
        height: Grid height
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize cell age tracker."""
        self.width = width
        self.height = height
        self.age_grid = np.zeros((height, width), dtype=np.int32)
        self.max_age_seen = 0

    def update(self, current_grid: np.ndarray) -> None:
        """Update age tracking based on current grid state.

        Args:
            current_grid: Current grid state (0=dead, 1+=alive)
        """
        # Increment age for living cells
        alive_mask = current_grid > 0
        self.age_grid[alive_mask] += 1

        # Reset age for dead cells
        dead_mask = current_grid == 0
        self.age_grid[dead_mask] = 0

        # Track maximum age
        current_max = self.age_grid.max()
        if current_max > self.max_age_seen:
            self.max_age_seen = current_max

    def reset(self) -> None:
        """Reset all cell ages to zero."""
        self.age_grid.fill(0)
        self.max_age_seen = 0

    def get_age_grid(self) -> np.ndarray:
        """Get the current age grid.

        Returns:
            2D array of cell ages
        """
        return self.age_grid.copy()

    def get_statistics(self) -> dict:
        """Get statistics about cell ages.

        Returns:
            Dictionary with age statistics
        """
        alive_cells = self.age_grid[self.age_grid > 0]

        if len(alive_cells) == 0:
            return {
                "max_age": 0,
                "mean_age": 0.0,
                "median_age": 0.0,
                "young_cells": 0,  # age 1-5
                "mature_cells": 0,  # age 6-20
                "ancient_cells": 0,  # age > 20
            }

        young = (alive_cells >= 1) & (alive_cells <= 5)
        mature = (alive_cells > 5) & (alive_cells <= 20)
        return {
            "max_age": int(self.age_grid.max()),
            "mean_age": float(alive_cells.mean()),
            "median_age": float(np.median(alive_cells)),
            "young_cells": int(np.sum(young)),
            "mature_cells": int(np.sum(mature)),
            "ancient_cells": int(np.sum(alive_cells > 20)),
        }

    def get_heatmap_colors(
        self, colormap: str = "fire"
    ) -> Optional[np.ndarray]:
        """Get RGB colors for age-based heatmap visualization.

        Args:
            colormap: Color scheme ('fire', 'ice', 'rainbow')

        Returns:
            3D array (height, width, 3) with RGB values, or None
        """
        if self.max_age_seen == 0:
            return None

        height, width = self.age_grid.shape
        colors = np.zeros((height, width, 3), dtype=np.uint8)

        # Normalize ages to 0-1 range
        normalized = self.age_grid.astype(float) / max(self.max_age_seen, 1)

        if colormap == "fire":
            # Black -> Red -> Yellow -> White
            colors[:, :, 0] = (normalized * 255).astype(np.uint8)  # Red
            colors[:, :, 1] = (np.clip(normalized * 2 - 1, 0, 1) * 255).astype(
                np.uint8
            )  # Green
            colors[:, :, 2] = (np.clip(normalized * 3 - 2, 0, 1) * 255).astype(
                np.uint8
            )  # Blue
        elif colormap == "ice":
            # Black -> Blue -> Cyan -> White
            colors[:, :, 0] = (np.clip(normalized * 2 - 1, 0, 1) * 255).astype(
                np.uint8
            )  # Red
            colors[:, :, 1] = (np.clip(normalized * 2 - 1, 0, 1) * 255).astype(
                np.uint8
            )  # Green
            colors[:, :, 2] = (normalized * 255).astype(np.uint8)  # Blue
        elif colormap == "rainbow":
            # Full spectrum: Red -> Yellow -> Green -> Cyan -> Blue -> Magenta
            hue = normalized * 300  # 0-300 degrees
            # Convert HSV to RGB (simplified)
            colors[:, :, 0] = (
                np.clip(np.abs(hue - 180) - 60, 0, 120) / 120 * 255
            ).astype(np.uint8)
            colors[:, :, 1] = (
                np.clip(120 - np.abs(hue - 120), 0, 120) / 120 * 255
            ).astype(np.uint8)
            colors[:, :, 2] = (
                np.clip(120 - np.abs(hue - 240), 0, 120) / 120 * 255
            ).astype(np.uint8)

        # Make dead cells black
        dead_mask = self.age_grid == 0
        colors[dead_mask] = [0, 0, 0]

        return colors


class CellHistoryTracker:
    """Track cell state changes over time for analysis.

    Maintains a history of births, deaths, and state transitions.

    Args:
        max_history: Maximum number of states to track
    """

    def __init__(self, max_history: int = 100) -> None:
        """Initialize history tracker."""
        self.max_history = max_history
        self.history: list[dict] = []
        self.birth_counts: list[int] = []
        self.death_counts: list[int] = []

    def record(
        self,
        generation: int,
        grid: np.ndarray,
        previous_grid: Optional[np.ndarray] = None,
    ) -> None:
        """Record a generation's state.

        Args:
            generation: Generation number
            grid: Current grid state
            previous_grid: Previous grid state for computing changes
        """
        population = int(np.sum(grid > 0))

        births = 0
        deaths = 0

        if previous_grid is not None:
            # Count births (was 0, now >0)
            births = int(np.sum((previous_grid == 0) & (grid > 0)))
            # Count deaths (was >0, now 0)
            deaths = int(np.sum((previous_grid > 0) & (grid == 0)))

        record = {
            "generation": generation,
            "population": population,
            "births": births,
            "deaths": deaths,
        }

        self.history.append(record)
        self.birth_counts.append(births)
        self.death_counts.append(deaths)

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.birth_counts.pop(0)
            self.death_counts.pop(0)

    def clear(self) -> None:
        """Clear all history."""
        self.history.clear()
        self.birth_counts.clear()
        self.death_counts.clear()

    def get_statistics(self) -> dict:
        """Get aggregate statistics from history.

        Returns:
            Dictionary with historical statistics
        """
        if not self.history:
            return {
                "total_generations": 0,
                "avg_population": 0.0,
                "avg_births": 0.0,
                "avg_deaths": 0.0,
                "max_population": 0,
                "min_population": 0,
            }

        populations = [h["population"] for h in self.history]

        return {
            "total_generations": len(self.history),
            "avg_population": float(np.mean(populations)),
            "avg_births": float(np.mean(self.birth_counts)),
            "avg_deaths": float(np.mean(self.death_counts)),
            "max_population": int(np.max(populations)),
            "min_population": int(np.min(populations)),
        }
