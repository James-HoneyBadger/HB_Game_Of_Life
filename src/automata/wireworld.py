"""Wireworld cellular automaton implementation."""

from __future__ import annotations

import numpy as np

from core.boundary import convolve_with_boundary
from .base import CellularAutomaton


class Wireworld(CellularAutomaton):
    """Wireworld with four states: empty, head, tail, conductor."""

    STATE_COUNT = 4

    EMPTY = 0
    HEAD = 1
    TAIL = 2
    CONDUCTOR = 3

    def __init__(self, width: int, height: int) -> None:
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        """Clear to an empty grid."""

        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Load a simple preset pattern."""

        self.reset()
        if pattern_name == "Random Soup":
            # Randomly sprinkle conductors and a few heads to start activity
            conductor_mask = self.rng.random(self.grid.shape) < 0.1
            head_mask = self.rng.random(self.grid.shape) < 0.02
            self.grid[conductor_mask] = self.CONDUCTOR
            self.grid[head_mask] = self.HEAD
        elif pattern_name != "Empty":
            raise ValueError(f"Unsupported pattern for Wireworld: {pattern_name}")

    def step(self) -> None:
        """Advance one generation according to Wireworld rules."""

        kernel = np.ones((3, 3), dtype=int)
        kernel[1, 1] = 0
        head_neighbors = convolve_with_boundary(
            (self.grid == self.HEAD).astype(int),
            kernel,
            self.boundary_mode,
        )

        new_grid = np.copy(self.grid)
        new_grid[self.grid == self.EMPTY] = self.EMPTY
        new_grid[self.grid == self.HEAD] = self.TAIL
        new_grid[self.grid == self.TAIL] = self.CONDUCTOR

        conductor_mask = self.grid == self.CONDUCTOR
        births = (head_neighbors == 1) | (head_neighbors == 2)
        new_grid[conductor_mask & births] = self.HEAD
        new_grid[conductor_mask & ~births] = self.CONDUCTOR

        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        """Cycle through states for quick editing."""

        current = int(self.grid[y, x])
        next_state = (current + 1) % 4
        self.grid[y, x] = next_state
