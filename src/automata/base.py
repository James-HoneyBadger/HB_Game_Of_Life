"""Base class for cellular automata"""

from abc import ABC, abstractmethod

import numpy as np

from core.boundary import BoundaryMode
from scenarios import build_scenario, get_scenario_names, resolve_scenario_name


class CellularAutomaton(ABC):
    """Base class for cellular automaton implementations."""

    STATE_COUNT = 2

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.boundary_mode = BoundaryMode.WRAP
        self.rng = np.random.default_rng()
        # Derived classes should initialize this
        self.grid: np.ndarray = np.zeros((height, width), dtype=int)
        self.reset()

    @abstractmethod
    def reset(self) -> None:
        """Reset the automaton to its initial state."""

    @abstractmethod
    def step(self) -> None:
        """Advance the simulation by one generation."""

    @abstractmethod
    def get_grid(self) -> np.ndarray:
        """Return the current grid state for rendering."""

    @abstractmethod
    def handle_click(self, x: int, y: int) -> None:
        """Handle mouse click at grid position ``(x, y)``."""

    def set_cell(self, x: int, y: int, value: int = 1) -> None:
        """Set a cell using the common ``x, y`` coordinate convention."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = value

    def load_pattern(self, pattern_name: str) -> None:
        """Load a common empty or random starting pattern.

        Specialized automata override this for richer presets. The default
        implementation keeps every automaton usable through the same API.
        """
        self.reset()
        if pattern_name == "Empty":
            return
        if pattern_name == "Random Soup":
            random_mask = self.rng.random(self.grid.shape) < 0.15
            self.grid[random_mask] = 1
            return
        try:
            resolved_name = resolve_scenario_name(pattern_name)
        except ValueError:
            resolved_name = None
        if resolved_name is not None and resolved_name in get_scenario_names():
            self.grid = build_scenario(resolved_name, self.width, self.height)
            return
        raise ValueError(f"Unsupported pattern for {type(self).__name__}: {pattern_name}")

    def get_state_count(self) -> int:
        """Return the number of states represented by the automaton."""
        return int(self.STATE_COUNT)

    def set_boundary_mode(self, mode: BoundaryMode | str) -> None:
        """Set the boundary behavior used by the next generation."""
        self.boundary_mode = (
            mode if isinstance(mode, BoundaryMode)
            else BoundaryMode.from_string(mode)
        )

    def set_rng(self, rng: np.random.Generator) -> None:
        """Use an externally owned random generator for pattern loading."""
        self.rng = rng

    def get_internal_state(self) -> dict:
        """Return non-grid state required for persistence."""
        return {}

    def restore_internal_state(self, state: dict) -> None:
        """Restore non-grid state from a persistence payload."""
        if state:
            raise ValueError(
                f"Unsupported internal state for {type(self).__name__}"
            )
