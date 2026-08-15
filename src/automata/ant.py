"""Langton's Ant implementation."""

from __future__ import annotations

import numpy as np

from core.boundary import BoundaryMode
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

        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[self.ant_dir]
        next_x = self.ant_x + dx
        next_y = self.ant_y + dy
        if self.boundary_mode == BoundaryMode.WRAP:
            self.ant_x = next_x % self.width
            self.ant_y = next_y % self.height
        elif 0 <= next_x < self.width and 0 <= next_y < self.height:
            self.ant_x = next_x
            self.ant_y = next_y
        else:
            # Fixed and reflected boundaries keep the ant on the grid and
            # turn it around when the next move would leave the world.
            self.ant_dir = (self.ant_dir + 2) % 4

    def get_grid(self) -> np.ndarray:
        display_grid = self.grid.copy()
        display_grid[self.ant_y, self.ant_x] = 2
        return display_grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        self.ant_x = x
        self.ant_y = y

    def get_internal_state(self) -> dict:
        """Return the ant position and heading for persistence."""
        return {
            "ant_x": self.ant_x,
            "ant_y": self.ant_y,
            "ant_dir": self.ant_dir,
        }

    def restore_internal_state(self, state: dict) -> None:
        self.ant_x = int(state["ant_x"])
        self.ant_y = int(state["ant_y"])
        self.ant_dir = int(state["ant_dir"]) % 4
