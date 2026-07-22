"""Brian's Brain cellular automaton implementation."""

# pylint: disable=duplicate-code

from __future__ import annotations

import numpy as np
from scipy import signal

from .base import CellularAutomaton


class BriansBrain(CellularAutomaton):
    """Brian's Brain with states: off (0), firing (1), refractory (2)."""

    OFF = 0
    FIRING = 1
    REFRACTORY = 2

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Load a named pattern into the grid."""
        self.reset()
        if pattern_name == "Random Soup":
            mask = np.random.random(self.grid.shape) < 0.08
            self.grid[mask] = self.FIRING

    def step(self) -> None:
        """Advance by one generation."""

        kernel = np.ones((3, 3), dtype=int)
        kernel[1, 1] = 0
        firing_neighbors = signal.convolve2d(
            (self.grid == self.FIRING).astype(int),
            kernel,
            mode="same",
            boundary="wrap",
        )

        births = (self.grid == self.OFF) & (firing_neighbors == 2)
        new_grid = np.zeros_like(self.grid)
        new_grid[births] = self.FIRING
        new_grid[self.grid == self.FIRING] = self.REFRACTORY
        new_grid[self.grid == self.REFRACTORY] = self.OFF
        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        """Toggle between off and firing for easy painting."""

        self.grid[y, x] = self.OFF if self.grid[y, x] else self.FIRING
