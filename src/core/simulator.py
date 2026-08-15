"""Core simulator logic decoupled from GUI."""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from automata import CellularAutomaton, LifeLikeAutomaton

from .config import SimulatorConfig
from .metrics import calculate_transition_metrics
from .registry import get_mode, normalize_mode
from .undo_manager import UndoManager


class Simulator:
    """High-level simulation engine independent of GUI.

    This provides a clean API for running cellular automaton simulations,
    suitable for CLI, notebooks, or other integrations beyond the GUI.
    """

    def __init__(self, config: Optional[SimulatorConfig] = None) -> None:
        """Initialize simulator with configuration.

        Args:
            config: SimulatorConfig instance or None for defaults
        """
        self.config = config or SimulatorConfig()
        if self.config.max_cycle_states < 1:
            raise ValueError("max_cycle_states must be greater than zero")
        self.automaton: Optional[CellularAutomaton] = None
        self.generation = 0
        self.metrics_log: list[dict] = []
        self.undo_manager = UndoManager()
        self._on_step_callback: Optional[Callable[[dict], None]] = None
        self._seen_states: dict[bytes, int] = {}
        self._cycle_start: Optional[int] = None
        self._cycle_period: Optional[int] = None
        self.rng = np.random.default_rng(self.config.seed)

    def initialize(
        self, mode: Optional[str] = None, pattern: Optional[str] = None
    ) -> None:
        """Initialize the automaton.

        Args:
            mode: Automaton mode name, or use config default
            pattern: Pattern preset to load
        """
        mode = normalize_mode(mode or self.config.automaton_mode)
        self.config.automaton_mode = mode
        descriptor = get_mode(mode)

        if mode == "Custom Rules" or (
            self.config.birth_rule and self.config.survival_rule
        ):
            self.automaton = LifeLikeAutomaton(
                self.config.width,
                self.config.height,
                birth=self.config.birth_rule,
                survival=self.config.survival_rule,
            )
        else:
            assert descriptor.factory is not None
            self.automaton = descriptor.factory(
                self.config.width, self.config.height
            )
        self.automaton.set_boundary_mode(self.config.boundary_mode)
        self.automaton.set_rng(self.rng)

        self.reset_metrics()

        if pattern:
            self.automaton.load_pattern(pattern)
        self._reset_cycle_detection()

    def reset(self) -> None:
        """Reset the automaton to initial state."""
        if self.automaton:
            self.automaton.reset()
            self.reset_metrics()

    def load_pattern(self, pattern_name: str) -> None:
        """Load a pattern and start a fresh simulation history."""
        if self.automaton is None:
            raise RuntimeError("Automaton not initialized")
        self.automaton.load_pattern(pattern_name)
        self.reset_metrics()

    def replace_grid(self, grid: np.ndarray) -> None:
        """Replace raw grid state and start a fresh simulation history."""
        if self.automaton is None:
            raise RuntimeError("Automaton not initialized")
        expected_shape = (self.config.height, self.config.width)
        if grid.shape != expected_shape or grid.ndim != 2:
            raise ValueError(
                f"Grid shape {grid.shape} does not match {expected_shape}"
            )
        self.automaton.grid = np.asarray(grid, dtype=int).copy()
        self.reset_metrics()

    def reset_metrics(self) -> None:
        """Reset metrics while keeping automaton."""
        self.generation = 0
        self.metrics_log.clear()
        self.undo_manager.clear()
        self._reset_cycle_detection()

    def _reset_cycle_detection(self) -> None:
        """Start cycle tracking from the current grid state."""
        self._seen_states.clear()
        self._cycle_start = None
        self._cycle_period = None
        if self.config.enable_cycle_detection and self.automaton is not None:
            self._seen_states[self._raw_grid().tobytes()] = (
                self.generation
            )

    def _raw_grid(self) -> np.ndarray:
        """Return simulation state without renderer-only overlays."""
        if self.automaton is None:
            raise RuntimeError("Automaton not initialized")
        return self.automaton.grid

    def _record_cycle_state(self, grid: np.ndarray) -> None:
        """Record a grid and capture the first repeated-state cycle."""
        if not self.config.enable_cycle_detection or self._cycle_period:
            return
        state_key = grid.tobytes()
        previous_generation = self._seen_states.get(state_key)
        if previous_generation is not None:
            self._cycle_start = previous_generation
            self._cycle_period = self.generation - previous_generation
        else:
            if len(self._seen_states) >= self.config.max_cycle_states:
                oldest_key = next(iter(self._seen_states))
                del self._seen_states[oldest_key]
            self._seen_states[state_key] = self.generation

    def step(self, num_steps: int = 1) -> list[dict]:
        """Advance simulation by N steps.

        Args:
            num_steps: Number of generations to advance

        Returns:
            List of metric dicts for each step
        """
        if num_steps < 0:
            raise ValueError("num_steps must be zero or greater")
        if not self.automaton:
            raise RuntimeError(
                "Automaton not initialized. Call initialize() first."
            )

        step_metrics = []

        for _ in range(num_steps):
            # Save state for undo before stepping
            previous_grid = np.copy(self._raw_grid())
            self.undo_manager.push_state(
                f"Generation {self.generation}",
                previous_grid,
            )

            self.automaton.step()
            self.generation += 1

            grid = self._raw_grid()
            self._record_cycle_state(grid)
            metrics = calculate_transition_metrics(
                previous_grid,
                grid,
                self.generation,
                self.automaton.get_state_count(),
            )

            self.metrics_log.append(metrics)
            step_metrics.append(metrics)

            if self._on_step_callback:
                self._on_step_callback(metrics)

        return step_metrics

    def set_cell(self, x: int, y: int, value: int = 1) -> None:
        """Set a cell value directly.

        Args:
            x: X coordinate
            y: Y coordinate
            value: Cell value (usually 0 or 1)
        """
        if not self.automaton:
            raise RuntimeError("Automaton not initialized.")

        if value < 0 or value >= self.automaton.get_state_count():
            raise ValueError(
                f"Cell value must be in range 0.."
                f"{self.automaton.get_state_count() - 1}"
            )

        grid = self._raw_grid()
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            grid[y, x] = value
            self.reset_metrics()

    def get_grid(self) -> np.ndarray:
        """Get current grid state.

        Returns:
            Current grid as numpy array
        """
        if not self.automaton:
            raise RuntimeError("Automaton not initialized.")
        return self.automaton.get_grid()

    def get_raw_grid(self) -> np.ndarray:
        """Get simulation state without renderer-only overlays."""
        return self._raw_grid()

    def estimate_memory_bytes(self) -> int:
        """Estimate grid and undo-history memory held by the simulator."""
        current = int(self._raw_grid().nbytes) if self.automaton else 0
        return current + self.undo_manager.memory_bytes()

    def undo(self) -> bool:
        """Undo the last step.

        Returns:
            True if undo was successful
        """
        if not self.automaton:
            return False
        current_grid = np.copy(self._raw_grid())
        result = self.undo_manager.undo(current_grid)
        if result:
            _, grid = result
            self.automaton.grid = np.copy(grid)
            self.generation = max(0, self.generation - 1)
            self._reset_cycle_detection()
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone step.

        Returns:
            True if redo was successful
        """
        if not self.automaton:
            return False
        current_grid = np.copy(self._raw_grid())
        result = self.undo_manager.redo(current_grid)
        if result:
            _, grid = result
            self.automaton.grid = np.copy(grid)
            self.generation += 1
            self._reset_cycle_detection()
            return True
        return False

    def set_on_step_callback(
        self, callback: Optional[Callable[[dict], None]]
    ) -> None:
        """Set callback to be called on each step.

        Args:
            callback: Function that receives metric dict
        """
        self._on_step_callback = callback

    def get_metrics_summary(self) -> dict:
        """Get summary of metrics.

        Returns:
            Dict with simulation statistics
        """
        if not self.metrics_log:
            if self.automaton is not None:
                grid = self._raw_grid()
                population = int(np.count_nonzero(grid))
                state_counts = {
                    str(state): int(np.count_nonzero(grid == state))
                    for state in range(self.automaton.get_state_count())
                }
                density = float(population / grid.size)
            else:
                population = 0
                state_counts = {}
                density = 0.0
            return {
                "generations": 0,
                "current_population": population,
                "max_population": population,
                "avg_density": density,
                "births": 0,
                "deaths": 0,
                "state_counts": state_counts,
                "undo_available": self.undo_manager.can_undo(),
                "redo_available": self.undo_manager.can_redo(),
                "cycle_detected": self._cycle_period is not None,
                "cycle_start": self._cycle_start,
                "cycle_period": self._cycle_period,
            }

        populations = [m["population"] for m in self.metrics_log]
        densities = [m["density"] for m in self.metrics_log]

        return {
            "generations": len(self.metrics_log),
            "current_population": populations[-1] if populations else 0,
            "max_population": max(populations) if populations else 0,
            "avg_density": (
                sum(densities) / len(densities) if densities else 0.0
            ),
            "births": self.metrics_log[-1]["births"],
            "deaths": self.metrics_log[-1]["deaths"],
            "state_counts": self.metrics_log[-1]["state_counts"],
            "undo_available": self.undo_manager.can_undo(),
            "redo_available": self.undo_manager.can_redo(),
            "cycle_detected": self._cycle_period is not None,
            "cycle_start": self._cycle_start,
            "cycle_period": self._cycle_period,
        }
