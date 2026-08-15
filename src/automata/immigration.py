# pylint: disable=duplicate-code

"""Immigration Game automaton (multi-state)."""

from __future__ import annotations

import numpy as np

from core.boundary import convolve_with_boundary
from .base import CellularAutomaton


class ImmigrationGame(CellularAutomaton):
    """Immigration Game - multi-color variant with Conway rules."""

    STATE_COUNT = 4

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Populate the grid with a named preset or clear state."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        if pattern_name == "Empty":
            return
        center_x = self.width // 2
        center_y = self.height // 2

        if pattern_name == "Color Mix":
            self._add_color_mix(center_x, center_y)
        elif pattern_name == "Random Soup":
            self._add_random_soup()
        else:
            raise ValueError(f"Unsupported pattern for ImmigrationGame: {pattern_name}")

    def _add_color_mix(self, center_x: int, center_y: int) -> None:
        glider1 = [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]
        for dx, dy in glider1:
            x, y = center_x - 20 + dx, center_y - 15 + dy
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y, x] = 1

        blinker2 = [(0, 0), (1, 0), (2, 0)]
        for dx, dy in blinker2:
            x, y = center_x + dx - 1, center_y - 15 + dy
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y, x] = 2

        block3 = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for dx, dy in block3:
            x, y = center_x + 10 + dx, center_y - 15 + dy
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y, x] = 3

    def _add_random_soup(self) -> None:
        random_mask = self.rng.random(self.grid.shape) < 0.15
        random_states = self.rng.integers(1, 4, size=self.grid.shape)
        self.grid[random_mask] = random_states[random_mask]

    def step(self) -> None:
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        alive_mask = self.grid > 0
        neighbor_count = convolve_with_boundary(
            alive_mask.astype(int), kernel, self.boundary_mode
        )
        color_sum = convolve_with_boundary(
            self.grid, kernel, self.boundary_mode
        )

        neighbors_2_or_3 = (neighbor_count == 2) | (neighbor_count == 3)
        survive_mask = alive_mask & neighbors_2_or_3
        birth_mask = (~alive_mask) & (neighbor_count == 3)

        new_grid = np.zeros_like(self.grid)
        new_grid[survive_mask] = self.grid[survive_mask]

        avg_state = np.zeros_like(self.grid)
        avg_state[birth_mask] = color_sum[birth_mask] // 3
        new_grid[birth_mask] = (avg_state[birth_mask] % 3) + 1

        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        self.grid[y, x] = (self.grid[y, x] + 1) % 4
