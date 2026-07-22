"""
Statistics collection and export for cellular automaton simulations.

This module provides tools for collecting simulation metrics and exporting
them to CSV format for analysis and visualization.
"""

import csv
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class SimulationStatistics:
    """Statistics for a single simulation step.

    Attributes:
        step: Step number
        timestamp: Time when recorded
        alive_cells: Number of alive/active cells
        dead_cells: Number of dead/inactive cells
        density: Proportion of alive cells (0-1)
        births: Number of cells born this step
        deaths: Number of cells that died this step
        stability: Measure of grid stability (0-1)
        entropy: Shannon entropy of the grid
        metadata: Additional custom metrics
    """

    # pylint: disable=too-many-instance-attributes

    step: int
    timestamp: float
    alive_cells: int
    dead_cells: int
    density: float
    births: int = 0
    deaths: int = 0
    stability: float = 0.0
    entropy: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Flatten metadata
        metadata = data.pop("metadata", {})
        data.update({f"meta_{k}": v for k, v in metadata.items()})
        return data


class StatisticsCollector:
    """Collect statistics during simulation.

    This class tracks various metrics about the simulation state
    over time, enabling analysis of population dynamics, stability,
    and other emergent behaviors.

    Args:
        track_changes: Whether to track births/deaths between steps
        calculate_entropy: Whether to calculate grid entropy
    """

    def __init__(
        self, track_changes: bool = True, calculate_entropy: bool = False
    ):
        self.track_changes = track_changes
        self.calculate_entropy = calculate_entropy
        self.statistics: List[SimulationStatistics] = []
        self._previous_grid: Optional[np.ndarray] = None
        self._start_time = time.time()

    def collect(
        self,
        step: int,
        grid: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SimulationStatistics:
        """Collect statistics for the current step.

        Args:
            step: Current step number
            grid: Current grid state
            metadata: Optional additional metrics

        Returns:
            SimulationStatistics object
        """
        # Count alive and dead cells
        alive_cells = int(np.count_nonzero(grid))
        total_cells = int(grid.size)
        dead_cells = total_cells - alive_cells
        density = alive_cells / total_cells if total_cells > 0 else 0.0

        # Calculate changes from previous step
        births = 0
        deaths = 0
        stability = 1.0

        if self.track_changes and self._previous_grid is not None:
            # Births: cells that were dead and are now alive
            births = int(np.sum((self._previous_grid == 0) & (grid != 0)))
            # Deaths: cells that were alive and are now dead
            deaths = int(np.sum((self._previous_grid != 0) & (grid == 0)))
            # Stability: proportion of cells that didn't change
            unchanged = np.sum((self._previous_grid == 0) == (grid == 0))
            stability = unchanged / total_cells if total_cells > 0 else 1.0

        # Calculate entropy if requested
        entropy = 0.0
        if self.calculate_entropy:
            entropy = self._calculate_entropy(grid)

        # Create statistics object
        stats = SimulationStatistics(
            step=step,
            timestamp=time.time() - self._start_time,
            alive_cells=alive_cells,
            dead_cells=dead_cells,
            density=density,
            births=int(births),
            deaths=int(deaths),
            stability=stability,
            entropy=entropy,
            metadata=metadata or {},
        )

        self.statistics.append(stats)
        self._previous_grid = grid.copy()

        return stats

    def _calculate_entropy(self, grid: np.ndarray) -> float:
        """Calculate Shannon entropy of the grid.

        Args:
            grid: Grid to analyze

        Returns:
            Entropy value
        """
        # Get unique values and their counts
        unique, counts = np.unique(grid, return_counts=True)

        if len(unique) <= 1:
            return 0.0

        # Calculate probabilities
        probabilities = counts / grid.size

        # Calculate entropy: -sum(p * log2(p))
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

        return float(entropy)

    def get_statistics(self) -> List[SimulationStatistics]:
        """Get all collected statistics.

        Returns:
            List of SimulationStatistics objects
        """
        return self.statistics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all steps.

        Returns:
            Dictionary with summary metrics
        """
        if not self.statistics:
            return {}

        densities = [s.density for s in self.statistics]
        births = [s.births for s in self.statistics]
        deaths = [s.deaths for s in self.statistics]
        stabilities = [s.stability for s in self.statistics]

        return {
            "total_steps": len(self.statistics),
            "duration": (
                self.statistics[-1].timestamp if self.statistics else 0
            ),
            "avg_density": np.mean(densities),
            "min_density": np.min(densities),
            "max_density": np.max(densities),
            "avg_births": np.mean(births),
            "avg_deaths": np.mean(deaths),
            "avg_stability": np.mean(stabilities),
            "final_alive": self.statistics[-1].alive_cells,
            "final_dead": self.statistics[-1].dead_cells,
        }

    def reset(self) -> None:
        """Reset the collector."""
        self.statistics.clear()
        self._previous_grid = None
        self._start_time = time.time()


class StatisticsExporter:
    """Export statistics to various formats.

    This class handles exporting collected statistics to CSV files
    and can generate basic plots if matplotlib is available.
    """

    @staticmethod
    def export_csv(
        statistics: List[SimulationStatistics],
        filepath: str,
        include_metadata: bool = True,
    ) -> None:
        """Export statistics to CSV file.

        Args:
            statistics: List of statistics to export
            filepath: Path to output CSV file
            include_metadata: Whether to include metadata columns
        """
        if not statistics:
            raise ValueError("No statistics to export")

        # Convert to dictionaries
        rows = [s.to_dict() for s in statistics]

        # Get all field names
        fieldnames = list(rows[0].keys())

        # Optionally remove metadata fields
        if not include_metadata:
            fieldnames = [f for f in fieldnames if not f.startswith("meta_")]
            rows = [
                {k: v for k, v in row.items() if not k.startswith("meta_")}
                for row in rows
            ]

        # Write CSV
        with open(
            filepath, "w", newline="", encoding="utf-8"
        ) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def export_summary(
        statistics: List[SimulationStatistics], filepath: str
    ) -> None:
        """Export summary statistics to CSV.

        Args:
            statistics: List of statistics
            filepath: Path to output CSV file
        """
        if not statistics:
            raise ValueError("No statistics to export")

        collector = StatisticsCollector()
        collector.statistics = statistics
        summary = collector.get_summary()

        # Write summary CSV
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=summary.keys())
            writer.writeheader()
            writer.writerow(summary)

    @staticmethod
    def generate_plots(
        statistics: List[SimulationStatistics],
        output_dir: str,
        plot_types: Optional[List[str]] = None,
    ) -> List[str]:
        """Generate plots from statistics.

        Args:
            statistics: List of statistics
            output_dir: Directory to save plots
            plot_types: Types of plots to generate
                (density, births_deaths, stability)

        Returns:
            List of generated file paths

        Raises:
            ImportError: If matplotlib is not available
        """
        # pylint: disable=import-outside-toplevel, too-many-statements
        try:
            import matplotlib  # type: ignore[import-not-found]

            matplotlib.use("Agg")  # Use non-interactive backend
            import matplotlib.pyplot as plt  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "matplotlib is required for plot generation. "
                "Install with: pip install matplotlib"
            ) from exc

        if not statistics:
            raise ValueError("No statistics to plot")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        plot_types = plot_types or ["density", "births_deaths", "stability"]
        generated_files = []

        steps = [s.step for s in statistics]

        # Density plot
        if "density" in plot_types:
            plt.figure(figsize=(10, 6))
            densities = [s.density for s in statistics]
            plt.plot(steps, densities, linewidth=2)
            plt.xlabel("Step")
            plt.ylabel("Density")
            plt.title("Cell Density Over Time")
            plt.grid(True, alpha=0.3)
            filepath = output_path / "density_plot.png"
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            generated_files.append(str(filepath))

        # Births and deaths plot
        if "births_deaths" in plot_types:
            plt.figure(figsize=(10, 6))
            births = [s.births for s in statistics]
            deaths = [s.deaths for s in statistics]
            plt.plot(steps, births, label="Births", linewidth=2)
            plt.plot(steps, deaths, label="Deaths", linewidth=2)
            plt.xlabel("Step")
            plt.ylabel("Count")
            plt.title("Births and Deaths Over Time")
            plt.legend()
            plt.grid(True, alpha=0.3)
            filepath = output_path / "births_deaths_plot.png"
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            generated_files.append(str(filepath))

        # Stability plot
        if "stability" in plot_types:
            plt.figure(figsize=(10, 6))
            stabilities = [s.stability for s in statistics]
            plt.plot(steps, stabilities, linewidth=2, color="green")
            plt.xlabel("Step")
            plt.ylabel("Stability")
            plt.title("Grid Stability Over Time")
            plt.ylim(0, 1.05)
            plt.grid(True, alpha=0.3)
            filepath = output_path / "stability_plot.png"
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            generated_files.append(str(filepath))

        return generated_files
