# pylint: disable=duplicate-code

"""Rainbow Game automaton."""

from __future__ import annotations

import numpy as np
from scipy import signal

from .base import CellularAutomaton


class RainbowGame(CellularAutomaton):
    """Rainbow Game - six color cellular automaton."""

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        """Reset grid to empty state."""
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Populate the grid with a named preset."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        center_x = self.width // 2
        center_y = self.height // 2

        if pattern_name == "Rainbow Mix":
            self._add_rainbow_mix(center_x, center_y)
        elif pattern_name == "Random Soup":
            self._add_random_soup()

    def _add_rainbow_mix(self, center_x: int, center_y: int) -> None:
        patterns = [
            (
                [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
                -30,
                -20,
                1,
            ),
            ([(0, 0), (1, 0), (2, 0)], -15, -20, 2),
            (
                [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)],
                0,
                -20,
                3,
            ),
            ([(0, 0), (1, 0), (0, 1), (1, 1)], 15, -20, 4),
            (
                [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)],
                25,
                -20,
                5,
            ),
            (
                [(0, 0), (1, 0), (0, 1), (3, 2), (2, 3), (3, 3)],
                -20,
                0,
                6,
            ),
        ]

        for pattern, offset_x, offset_y, state in patterns:
            for dx, dy in pattern:
                x, y = center_x + offset_x + dx, center_y + offset_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y, x] = state

    def _add_random_soup(self) -> None:
        random_mask = np.random.random(self.grid.shape) < 0.15
        random_states = np.random.randint(1, 7, size=self.grid.shape)
        self.grid[random_mask] = random_states[random_mask]

    def step(self) -> None:
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        alive_mask = self.grid > 0
        neighbor_count = signal.convolve2d(
            alive_mask.astype(int),
            kernel,
            mode="same",
            boundary="wrap",
        )
        color_sum = signal.convolve2d(
            self.grid,
            kernel,
            mode="same",
            boundary="wrap",
        )

        neighbors_2_or_3 = (neighbor_count == 2) | (neighbor_count == 3)
        survive_mask = alive_mask & neighbors_2_or_3
        birth_mask = (~alive_mask) & (neighbor_count == 3)

        new_grid = np.zeros_like(self.grid)
        new_grid[survive_mask] = self.grid[survive_mask]

        avg_color = np.zeros_like(self.grid)
        avg_color[birth_mask] = color_sum[birth_mask] // 3
        new_grid[birth_mask] = np.clip(
            avg_color[birth_mask],
            1,
            6,
        )

        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        self.grid[y, x] = (self.grid[y, x] + 1) % 7
