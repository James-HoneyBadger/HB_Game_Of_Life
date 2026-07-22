"""State containers for the GUI application."""

from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import dataclass, field
from io import StringIO
from typing import Deque, List, Optional

import numpy as np

from core.undo_manager import UndoManager
from automata import CellularAutomaton

from .config import DEFAULT_CELL_SIZE, DEFAULT_SPEED, MAX_HISTORY_LENGTH


# pylint: disable=too-many-instance-attributes
@dataclass
class SimulationState:
    """Mutable state shared by the GUI and simulation logic."""

    grid_width: int = 100
    grid_height: int = 100
    cell_size: int = DEFAULT_CELL_SIZE
    speed: int = DEFAULT_SPEED
    running: bool = False
    generation: int = 0
    show_grid: bool = True
    is_running: bool = False
    current_automaton: Optional[CellularAutomaton] = None
    population_history: Deque[int] = field(
        default_factory=lambda: deque(maxlen=MAX_HISTORY_LENGTH)
    )
    grid_history: Deque[np.ndarray] = field(
        default_factory=lambda: deque(maxlen=MAX_HISTORY_LENGTH)
    )
    undo_manager: UndoManager = field(
        default_factory=lambda: UndoManager(max_history=MAX_HISTORY_LENGTH)
    )
    population_peak: int = 0
    entropy_history: Deque[float] = field(
        default_factory=lambda: deque(maxlen=MAX_HISTORY_LENGTH)
    )
    complexity_history: Deque[int] = field(
        default_factory=lambda: deque(maxlen=MAX_HISTORY_LENGTH)
    )
    metrics_log: List[dict] = field(default_factory=list)
    seen_hashes: dict = field(default_factory=dict)
    cycle_period: Optional[int] = None
    cycle_first_seen: Optional[int] = None

    def reset_generation(self) -> None:
        """Reset generation counters and population history."""

        self.generation = 0
        self.population_history.clear()
        self.population_peak = 0
        self.entropy_history.clear()
        self.complexity_history.clear()
        self.metrics_log.clear()
        self.seen_hashes.clear()
        self.cycle_period = None
        self.cycle_first_seen = None
        self.grid_history.clear()

    def reset_metrics(self) -> None:
        """Reset metrics while keeping grid history intact."""

        self.generation = 0
        self.population_history.clear()
        self.population_peak = 0
        self.entropy_history.clear()
        self.complexity_history.clear()
        self.metrics_log.clear()
        self.seen_hashes.clear()
        self.cycle_period = None
        self.cycle_first_seen = None

    def update_population_stats(self, grid: np.ndarray) -> str:
        """Update population statistics and return the formatted label."""

        live_cells = int(np.count_nonzero(grid))
        history = self.population_history
        if history and history[-1] == live_cells:
            delta = 0
        else:
            previous = history[-1] if history else 0
            delta = live_cells - previous
            history.append(live_cells)
        self.population_peak = max(self.population_peak, live_cells)
        total = grid.size if grid.size else 1
        density = (live_cells / total) * 100

        # Calculate entropy (Shannon entropy of the grid)
        if 0 < live_cells < total:
            p_live = live_cells / total
            p_dead = 1 - p_live
            entropy = -(p_live * np.log2(p_live) + p_dead * np.log2(p_dead))
        else:
            entropy = 0.0
        self.entropy_history.append(entropy)

        # Calculate complexity (number of different 3x3 patterns)
        complexity = self._calculate_complexity(grid)
        self.complexity_history.append(complexity)

        # Cycle detection via hashed grid snapshots
        grid_hash = hash((grid.shape, grid.tobytes()))
        if grid_hash in self.seen_hashes:
            first_seen = self.seen_hashes[grid_hash]
            self.cycle_first_seen = first_seen
            self.cycle_period = self.generation - first_seen
        else:
            self.seen_hashes[grid_hash] = self.generation

        self.metrics_log.append(
            {
                "generation": self.generation,
                "live": live_cells,
                "delta": delta,
                "density": density,
                "entropy": entropy,
                "complexity": complexity,
                "cycle_period": self.cycle_period,
            }
        )

        parts = [
            f"Live: {live_cells}",
            f"Δ: {delta:+d}",
            f"Peak: {self.population_peak}",
            f"Density: {density:.1f}%",
            f"Entropy: {entropy:.2f}",
            f"Complexity: {complexity}",
        ]
        if self.cycle_period:
            parts.append(f"Cycle: {self.cycle_period}")
        return " | ".join(parts)

    def rebuild_stats_from_history(self) -> None:
        """Recompute metrics based on the stored grid history."""

        grids = list(self.grid_history)
        self.reset_metrics()
        # Restore generation count and metrics from snapshots
        for idx, grid in enumerate(grids):
            self.generation = idx
            self.update_population_stats(grid)

    def _calculate_complexity(self, grid: np.ndarray) -> int:
        """Calculate the number of unique 3x3 patterns in the grid."""
        if grid.size < 9:
            return 0

        patterns = set()
        h, w = grid.shape
        for i in range(h - 2):
            for j in range(w - 2):
                pattern = tuple(grid[i : i + 3, j : j + 3].flatten())
                patterns.add(pattern)
        return len(patterns)

    def add_metric(
        self, generation: int, population: int, peak: int, density: float
    ) -> None:
        """Add a metric entry to the log."""
        self.metrics_log.append(
            {
                "generation": generation,
                "population": population,
                "peak": peak,
                "density": density,
            }
        )

    def export_metrics_csv(self) -> str:
        """Export metrics as CSV string."""
        if not self.metrics_log:
            return ""

        output = StringIO()
        writer = csv.DictWriter(
            output, fieldnames=["generation", "population", "peak", "density"]
        )
        writer.writeheader()

        for metric in self.metrics_log:
            writer.writerow(
                {
                    "generation": metric.get("generation", ""),
                    "population": metric.get("population", ""),
                    "peak": metric.get("peak", ""),
                    "density": metric.get("density", ""),
                }
            )

        return output.getvalue()

    def save_state(self, filepath: str) -> None:
        """Save state to a JSON file."""
        state_data = {
            "cell_size": self.cell_size,
            "speed": self.speed,
            "generation": self.generation,
            "metrics_log": self.metrics_log,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

    def load_state(self, filepath: str) -> None:
        """Load state from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        self.cell_size = state_data.get("cell_size", DEFAULT_CELL_SIZE)
        self.speed = state_data.get("speed", DEFAULT_SPEED)
        self.generation = state_data.get("generation", 0)
        self.metrics_log = state_data.get("metrics_log", [])
