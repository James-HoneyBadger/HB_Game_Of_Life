"""Core simulator logic decoupled from GUI."""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from automata import (
    BriansBrain,
    CellularAutomaton,
    ConwayGameOfLife,
    GenerationsAutomaton,
    HighLife,
    ImmigrationGame,
    LangtonsAnt,
    LifeLikeAutomaton,
    RainbowGame,
    Wireworld,
)

from .config import SimulatorConfig
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
        self.automaton: Optional[CellularAutomaton] = None
        self.generation = 0
        self.metrics_log: list[dict] = []
        self.undo_manager = UndoManager()
        self._on_step_callback: Optional[Callable[[dict], None]] = None

        self._automaton_factories = {
            "Conway's Game of Life": ConwayGameOfLife,
            "HighLife": HighLife,
            "Langton's Ant": LangtonsAnt,
            "Wireworld": Wireworld,
            "Brian's Brain": BriansBrain,
            "Generations": GenerationsAutomaton,
            "Immigration": ImmigrationGame,
            "Rainbow": RainbowGame,
        }

    def initialize(
        self, mode: Optional[str] = None, pattern: Optional[str] = None
    ) -> None:
        """Initialize the automaton.

        Args:
            mode: Automaton mode name, or use config default
            pattern: Pattern preset to load
        """
        mode = mode or self.config.automaton_mode

        factory = self._automaton_factories.get(mode)
        if not factory:
            raise ValueError(f"Unknown automaton mode: {mode}")

        if mode in ["Wireworld", "Brian's Brain", "Generations"]:
            self.automaton = factory(self.config.width, self.config.height)
        elif mode == "Langton's Ant":
            self.automaton = factory(self.config.width, self.config.height)
        elif mode in ["Immigration", "Rainbow"]:
            self.automaton = factory(self.config.width, self.config.height)
        elif self.config.birth_rule and self.config.survival_rule:
            self.automaton = LifeLikeAutomaton(
                self.config.width,
                self.config.height,
                birth=self.config.birth_rule,
                survival=self.config.survival_rule,
            )
        else:
            self.automaton = factory(self.config.width, self.config.height)

        self.reset_metrics()

        if pattern and hasattr(self.automaton, "load_pattern"):
            self.automaton.load_pattern(pattern)

    def reset(self) -> None:
        """Reset the automaton to initial state."""
        if self.automaton:
            self.automaton.reset()
            self.reset_metrics()

    def reset_metrics(self) -> None:
        """Reset metrics while keeping automaton."""
        self.generation = 0
        self.metrics_log.clear()
        self.undo_manager.clear()

    def step(self, num_steps: int = 1) -> list[dict]:
        """Advance simulation by N steps.

        Args:
            num_steps: Number of generations to advance

        Returns:
            List of metric dicts for each step
        """
        if not self.automaton:
            raise RuntimeError(
                "Automaton not initialized. Call initialize() first."
            )

        step_metrics = []

        for _ in range(num_steps):
            # Save state for undo before stepping
            self.undo_manager.push_state(
                f"Generation {self.generation}",
                np.copy(self.automaton.get_grid()),
            )

            self.automaton.step()
            self.generation += 1

            grid = self.automaton.get_grid()
            metrics = {
                "generation": self.generation,
                "population": int(np.count_nonzero(grid)),
                "density": float(np.count_nonzero(grid) / grid.size),
            }

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

        grid = self.automaton.get_grid()
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            grid[y, x] = value

    def get_grid(self) -> np.ndarray:
        """Get current grid state.

        Returns:
            Current grid as numpy array
        """
        if not self.automaton:
            raise RuntimeError("Automaton not initialized.")
        return self.automaton.get_grid()

    def undo(self) -> bool:
        """Undo the last step.

        Returns:
            True if undo was successful
        """
        if not self.automaton:
            return False
        current_grid = np.copy(self.automaton.get_grid())
        result = self.undo_manager.undo(current_grid)
        if result:
            _, grid = result
            self.automaton.grid = np.copy(grid)
            self.generation = max(0, self.generation - 1)
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone step.

        Returns:
            True if redo was successful
        """
        if not self.automaton:
            return False
        current_grid = np.copy(self.automaton.get_grid())
        result = self.undo_manager.redo(current_grid)
        if result:
            _, grid = result
            self.automaton.grid = np.copy(grid)
            self.generation += 1
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
            return {"generations": 0}

        populations = [m["population"] for m in self.metrics_log]
        densities = [m["density"] for m in self.metrics_log]

        return {
            "generations": len(self.metrics_log),
            "current_population": populations[-1] if populations else 0,
            "max_population": max(populations) if populations else 0,
            "avg_density": (
                sum(densities) / len(densities) if densities else 0.0
            ),
            "undo_available": self.undo_manager.can_undo(),
            "redo_available": self.undo_manager.can_redo(),
        }
