# pylint: disable=duplicate-code

"""Generic life-like automaton with B/S rules."""

from __future__ import annotations

from typing import Iterable, Set, Tuple

import numpy as np
from scipy import signal

from .base import CellularAutomaton


def parse_bs(rule_str: str) -> Tuple[Set[int], Set[int]]:
    """Parse B/S rule notation like 'B3/S23' into birth/survival sets."""
    rule = rule_str.upper().replace(" ", "")
    b_part: Set[int] = set()
    s_part: Set[int] = set()

    if "B" in rule:
        try:
            start = rule.index("B") + 1
            end = rule.index("S") if "S" in rule else len(rule)
            segment = rule[start:end]
            b_part = {int(ch) for ch in segment if ch.isdigit()}
        except ValueError:
            b_part = set()

    if "S" in rule:
        try:
            start = rule.index("S") + 1
            segment = rule[start:]
            s_part = {int(ch) for ch in segment if ch.isdigit()}
        except ValueError:
            s_part = set()

    return b_part, s_part


class LifeLikeAutomaton(CellularAutomaton):
    """Generic life-like cellular automaton."""

    def __init__(
        self,
        width: int,
        height: int,
        birth: Iterable[int] | None = None,
        survival: Iterable[int] | None = None,
    ):
        self.birth = set(birth or {3})
        self.survival = set(survival or {2, 3})
        super().__init__(width, height)
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def set_rules(self, birth: Iterable[int], survival: Iterable[int]) -> None:
        """Update the birth and survival rule sets."""
        self.birth = set(birth)
        self.survival = set(survival)

    def reset(self) -> None:
        """Clear the grid to an all-dead state."""
        self.grid = np.zeros((self.height, self.width), dtype=int)

    def load_pattern(self, pattern_name: str) -> None:
        """Load a named preset onto the current grid."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        if pattern_name == "Random Soup":
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
        birth_any = (
            np.logical_or.reduce([(neighbors == n) for n in self.birth])
            if self.birth
            else np.zeros_like(self.grid, dtype=bool)
        )
        survival_any = (
            np.logical_or.reduce([(neighbors == n) for n in self.survival])
            if self.survival
            else np.zeros_like(self.grid, dtype=bool)
        )
        birth = (self.grid == 0) & birth_any
        survival = (self.grid == 1) & survival_any
        self.grid = (birth | survival).astype(int)

    def get_grid(self) -> np.ndarray:
        """Return the current grid state."""
        return self.grid  # type: ignore[no-any-return]

    def handle_click(self, x: int, y: int) -> None:
        """Toggle the state of a cell at the given coordinates."""
        self.grid[y, x] = 1 - self.grid[y, x]
