"""Hexagonal Game of Life implementation."""

import numpy as np

from core.boundary import roll_with_boundary
from .base import CellularAutomaton


class HexagonalGameOfLife(CellularAutomaton):
    """
    Hexagonal Cellular Automaton.

    Uses "Odd-r" horizontal layout (offset coordinates).
    Default Rule: "Hex Life" (B2/S34).
      - Birth on 2 neighbors.
      - Survival on 3 or 4 neighbors.
    """

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def step(self) -> None:
        """Calculate next state using hexagonal neighbors."""
        grid = self.grid

        # Directional shifts
        # Horizontal neighbors (always the same)
        # Left: (y, x-1), Right: (y, x+1)
        left = roll_with_boundary(grid, 1, axis=1, boundary=self.boundary_mode)
        right = roll_with_boundary(grid, -1, axis=1, boundary=self.boundary_mode)

        # Vertical/Diagonal shifts
        up = roll_with_boundary(grid, 1, axis=0, boundary=self.boundary_mode)
        down = roll_with_boundary(grid, -1, axis=0, boundary=self.boundary_mode)

        # Shifts combined with horizontal rolls
        up_left = roll_with_boundary(up, 1, axis=1, boundary=self.boundary_mode)
        up_right = roll_with_boundary(up, -1, axis=1, boundary=self.boundary_mode)
        down_left = roll_with_boundary(down, 1, axis=1, boundary=self.boundary_mode)
        down_right = roll_with_boundary(down, -1, axis=1, boundary=self.boundary_mode)

        # Neighbors for EVEN rows (y=0, 2, ...):
        # Connect to: Left, Right, Up-Left, Up, Down-Left, Down
        neighbors_even = left + right + up_left + up + down_left + down

        # Neighbors for ODD rows (y=1, 3, ...):
        # Connect to: Left, Right, Up, Up-Right, Down, Down-Right
        neighbors_odd = left + right + up + up_right + down + down_right

        # Combine based on row parity
        neighbors = np.zeros_like(grid, dtype=int)
        neighbors[0::2] = neighbors_even[0::2]
        neighbors[1::2] = neighbors_odd[1::2]

        # B2 / S34 Rule implementation
        # Birth: 2 neighbors
        birth = (grid == 0) & (neighbors == 2)
        # Survival: 3 or 4 neighbors
        survival = (grid == 1) & ((neighbors == 3) | (neighbors == 4))

        self.grid = (birth | survival).astype(int)

    def get_grid(self) -> np.ndarray:
        return self.grid

    def handle_click(self, x: int, y: int) -> None:
        """Toggle cell state.

        Note: The x, y passed here are grid coordinates (col, row),
        already converted by the UI layer from pixel inputs.
        """
        if 0 <= y < self.height and 0 <= x < self.width:
            self.grid[y, x] = 1 - self.grid[y, x]

    def load_pattern(self, pattern_name: str) -> None:
        """Load a pattern (only Random Soup supported for now)."""
        self.reset()
        if pattern_name == "Random Soup":
            self._add_random_soup()
        elif pattern_name != "Empty":
            raise ValueError(
                f"Unsupported pattern for HexagonalGameOfLife: {pattern_name}"
            )

    def _add_random_soup(self) -> None:
        random_mask = self.rng.random(self.grid.shape) < 0.15
        self.grid[random_mask] = 1
