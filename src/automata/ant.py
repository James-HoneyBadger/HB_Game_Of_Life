"""Langton's Ant implementation."""

from __future__ import annotations

import numpy as np

from .base import CellularAutomaton


class LangtonsAnt(CellularAutomaton):
    """Langton's Ant implementation."""

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        self.ant_x = width // 2
        self.ant_y = height // 2
        self.ant_dir = 0
        super().__init__(width, height)

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)
        self.ant_x = self.width // 2
        self.ant_y = self.height // 2
        self.ant_dir = 0  # 0=North, 1=East, 2=South, 3=West

    def step(self) -> None:
        current_color = self.grid[self.ant_y, self.ant_x]
        self.grid[self.ant_y, self.ant_x] = 1 - current_color

        if current_color == 0:
            self.ant_dir = (self.ant_dir + 1) % 4
        else:
            self.ant_dir = (self.ant_dir - 1) % 4

        if self.ant_dir == 0:
            self.ant_y = (self.ant_y - 1) % self.height
        elif self.ant_dir == 1:
            self.ant_x = (self.ant_x + 1) % self.width
        elif self.ant_dir == 2:
            self.ant_y = (self.ant_y + 1) % self.height
        else:
            self.ant_x = (self.ant_x - 1) % self.width

    def get_grid(self) -> np.ndarray:
        display_grid = self.grid.copy()
        display_grid[self.ant_y, self.ant_x] = 2
        return display_grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        self.ant_x = x
        self.ant_y = y
