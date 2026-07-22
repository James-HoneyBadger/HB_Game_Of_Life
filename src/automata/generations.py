"""Generations-style cellular automaton with fading states."""

# pylint: disable=duplicate-code

from __future__ import annotations

from typing import Iterable, Set

import numpy as np
from scipy import signal

from .base import CellularAutomaton


class GenerationsAutomaton(CellularAutomaton):
    """Life-like birth/survival with N fading states.

    State 1 stays alive, states 2..N-1 decay, then fade to 0.
    """

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        width: int,
        height: int,
        *,
        birth: Iterable[int] | None = None,
        survival: Iterable[int] | None = None,
        n_states: int = 8,
    ) -> None:
        self.birth: Set[int] = set(birth or {3})
        self.survival: Set[int] = set(survival or {2, 3})
        self.n_states = max(3, n_states)
        self.grid = np.zeros((height, width), dtype=int)
        super().__init__(width, height)

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Load a named pattern into the grid."""
        self.reset()
        if pattern_name == "Random Soup":
            mask = np.random.random(self.grid.shape) < 0.15
            self.grid[mask] = 1

    def set_rules(
        self,
        birth: Iterable[int],
        survival: Iterable[int],
        n_states: int | None = None,
    ) -> None:
        """Set birth/survival rules and optionally change state count."""
        self.birth = set(birth)
        self.survival = set(survival)
        if n_states:
            self.n_states = max(3, n_states)

    def step(self) -> None:
        """Advance one generation with fading states."""

        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        live_layer = (self.grid == 1).astype(int)
        neighbors = signal.convolve2d(
            live_layer,
            kernel,
            mode="same",
            boundary="wrap",
        )

        new_grid = np.copy(self.grid)

        births = (self.grid == 0) & np.isin(neighbors, list(self.birth))
        survive = (self.grid == 1) & np.isin(neighbors, list(self.survival))

        # Dead becomes alive on birth condition
        new_grid[births] = 1

        # Live survives, otherwise begins decay
        decays = (self.grid == 1) & ~survive
        new_grid[decays] = 2

        # Decaying states progress; last fades to 0
        decaying_mask = (self.grid >= 2) & (self.grid < self.n_states)
        new_grid[decaying_mask] = np.minimum(
            self.grid[decaying_mask] + 1,
            self.n_states - 1,
        )
        new_grid[self.grid == self.n_states - 1] = 0

        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        """Toggle cell state at the given coordinates."""
        self.grid[y, x] = (self.grid[y, x] + 1) % self.n_states
