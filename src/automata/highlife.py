# pylint: disable=duplicate-code

"""High Life (B36/S23) automaton."""

from __future__ import annotations

import numpy as np
from scipy import signal

from .base import CellularAutomaton


class HighLife(CellularAutomaton):
    """High Life - B36/S23 (replicators possible)."""

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        """Clear the grid to an empty state."""
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Populate the grid with the requested preset pattern."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        center_x = self.width // 2
        center_y = self.height // 2

        if pattern_name == "Replicator":
            self._add_replicator(center_x, center_y)
        elif pattern_name == "Random Soup":
            self._add_random_soup()

    def _add_replicator(self, center_x: int, center_y: int) -> None:
        """Place a replicator pattern centered at the given coordinates."""
        replicator = [(1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (2, 2), (1, 3)]
        for dx, dy in replicator:
            x, y = center_x + dx - 1, center_y + dy - 1
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y, x] = 1

    def _add_random_soup(self) -> None:
        """Scatter random live cells across the grid."""
        random_mask = np.random.random(self.grid.shape) < 0.15
        self.grid[random_mask] = 1

    def step(self) -> None:
        """Advance the automaton by one generation."""
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        neighbors = signal.convolve2d(
            self.grid,
            kernel,
            mode="same",
            boundary="wrap",
        )
        birth = (self.grid == 0) & ((neighbors == 3) | (neighbors == 6))
        survival = (self.grid == 1) & ((neighbors == 2) | (neighbors == 3))
        self.grid = (birth | survival).astype(int)

    def get_grid(self) -> np.ndarray:
        """Return the current grid state."""
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        """Toggle a single cell between alive and dead."""
        self.grid[y, x] = 1 - self.grid[y, x]
