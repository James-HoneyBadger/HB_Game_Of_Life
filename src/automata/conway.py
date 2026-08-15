# pylint: disable=duplicate-code

"""Conway's Game of Life implementation."""

from __future__ import annotations

import numpy as np

from core.boundary import convolve_with_boundary
from patterns import PATTERN_DATA
from scenarios import build_scenario, get_scenario_names

from .base import CellularAutomaton


class ConwayGameOfLife(CellularAutomaton):
    """Conway's Game of Life implementation."""

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        self._kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Load a predefined pattern onto the grid."""
        self.grid = np.zeros((self.height, self.width), dtype=int)

        if pattern_name == "Empty":
            return

        # Handle procedural patterns first
        if pattern_name == "Random Soup":
            self._add_random_soup()
            return

        if pattern_name in get_scenario_names():
            self.grid = build_scenario(pattern_name, self.width, self.height)
            return

        # Load from JSON-backed pattern data
        try:
            pattern_data_dict = PATTERN_DATA.get("Conway's Game of Life", {})

            if pattern_name in pattern_data_dict:
                points, _ = pattern_data_dict[pattern_name]
                if points:
                    center_x = self.width // 2
                    center_y = self.height // 2

                    for dx, dy in points:
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            self.grid[y, x] = 1
                return
        except ImportError:
            pass  # Fallback or silent fail if patterns module not found
        raise ValueError(
            f"Unsupported pattern for ConwayGameOfLife: {pattern_name}"
        )

    def _add_random_soup(self) -> None:
        random_mask = self.rng.random(self.grid.shape) < 0.15
        self.grid[random_mask] = 1

    def step(self) -> None:
        """Advance the automaton by one generation."""
        neighbors = convolve_with_boundary(
            self.grid, self._kernel, self.boundary_mode
        )
        self.grid = (
            ((self.grid == 1) & ((neighbors == 2) | (neighbors == 3)))
            | ((self.grid == 0) & (neighbors == 3))
        ).astype(int)

    def get_grid(self) -> np.ndarray:
        return self.grid

    def handle_click(self, x: int, y: int) -> None:
        self.grid[y, x] = 1 - self.grid[y, x]

    def get_available_patterns(self) -> list[str]:
        """Get list of available patterns for Conway's Game of Life."""
        try:
            pattern_data_dict = PATTERN_DATA.get("Conway's Game of Life", {})
            patterns = list(pattern_data_dict.keys())
            patterns.append("Random Soup")
            return sorted(patterns)
        except Exception:
            return ["Random Soup"]
