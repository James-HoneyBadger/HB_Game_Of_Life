"""
Advanced pattern analysis tools.

This module provides utilities for analyzing cellular automaton patterns,
detecting oscillators, still lifes, and other interesting structures.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from .visualization import SymmetryAnalyzer


@dataclass
class PatternMetrics:
    """Metrics describing a pattern.

    Attributes:
        bounding_box: (x, y, width, height) of pattern
        cell_count: Number of alive cells
        density: Proportion of alive cells in bounding box
        period: Oscillation period (0 if not periodic)
        is_still_life: Whether pattern is static
        is_oscillator: Whether pattern oscillates
        is_spaceship: Whether pattern moves
        velocity: Movement velocity (dx, dy) per step
        symmetries: List of detected symmetries
    """

    bounding_box: Tuple[int, int, int, int]
    cell_count: int
    density: float
    period: int = 0
    is_still_life: bool = False
    is_oscillator: bool = False
    is_spaceship: bool = False
    velocity: Tuple[float, float] = (0.0, 0.0)
    symmetries: List[str] = field(default_factory=list)


class PatternAnalyzer:
    """Analyze cellular automaton patterns.

    This class provides tools for detecting and analyzing various
    pattern types including still lifes, oscillators, and spaceships.
    """

    @staticmethod
    def get_bounding_box(grid: np.ndarray) -> Tuple[int, int, int, int]:
        """Get bounding box of alive cells.

        Args:
            grid: Grid to analyze

        Returns:
            Tuple of (x, y, width, height)
        """
        # Find coordinates of alive cells
        alive_coords = np.argwhere(grid != 0)

        if len(alive_coords) == 0:
            return (0, 0, 0, 0)

        # Get min/max coordinates
        min_y, min_x = alive_coords.min(axis=0)
        max_y, max_x = alive_coords.max(axis=0)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        return (int(min_x), int(min_y), int(width), int(height))

    @staticmethod
    def extract_pattern(
        grid: np.ndarray,
        bounding_box: Optional[Tuple[int, int, int, int]] = None,
    ) -> np.ndarray:
        """Extract pattern from grid.

        Args:
            grid: Source grid
            bounding_box: Optional bounding box, auto-detected if None

        Returns:
            Extracted pattern array
        """
        if bounding_box is None:
            bounding_box = PatternAnalyzer.get_bounding_box(grid)

        x, y, width, height = bounding_box

        if width == 0 or height == 0:
            return np.array([[]], dtype=grid.dtype)

        return grid[y:y + height, x:x + width].copy()

    @staticmethod
    def detect_period(
        grid_history: List[np.ndarray], max_period: int = 100
    ) -> int:
        """Detect oscillation period from grid history.

        Args:
            grid_history: List of grid states
            max_period: Maximum period to check

        Returns:
            Period (0 if not periodic or period > max_period)
        """
        if len(grid_history) < 2:
            return 0

        current = grid_history[-1]

        # Check periods from 1 to max_period
        for period in range(1, min(max_period + 1, len(grid_history))):
            if len(grid_history) < period + 1:
                break

            previous = grid_history[-(period + 1)]

            if np.array_equal(current, previous):
                # Verify period by checking more history if available
                verified = True
                checks = min(3, len(grid_history) // period)

                for i in range(1, checks):
                    idx = -(period * i + 1)
                    if -idx > len(grid_history):
                        break
                    if not np.array_equal(current, grid_history[idx]):
                        verified = False
                        break

                if verified:
                    return period

        return 0

    @staticmethod
    def detect_displacement(
        before: np.ndarray, after: np.ndarray
    ) -> Tuple[int, int]:
        """Detect pattern displacement between two grids.

        Args:
            before: Grid before
            after: Grid after

        Returns:
            Displacement tuple (dx, dy)
        """
        # Get bounding boxes
        bbox_before = PatternAnalyzer.get_bounding_box(before)
        bbox_after = PatternAnalyzer.get_bounding_box(after)

        if bbox_before[2] == 0 or bbox_after[2] == 0:
            return (0, 0)

        # Calculate displacement of center
        center_before_x = bbox_before[0] + bbox_before[2] / 2
        center_before_y = bbox_before[1] + bbox_before[3] / 2
        center_after_x = bbox_after[0] + bbox_after[2] / 2
        center_after_y = bbox_after[1] + bbox_after[3] / 2

        dx = int(round(center_after_x - center_before_x))
        dy = int(round(center_after_y - center_before_y))

        return (dx, dy)

    @staticmethod
    def analyze_pattern(
        grid_history: List[np.ndarray], check_symmetry: bool = True
    ) -> PatternMetrics:
        """Analyze a pattern from its history.

        Args:
            grid_history: List of grid states
            check_symmetry: Whether to analyze symmetries

        Returns:
            PatternMetrics object
        """
        if not grid_history:
            return PatternMetrics(
                bounding_box=(0, 0, 0, 0), cell_count=0, density=0.0
            )

        current = grid_history[-1]
        bbox = PatternAnalyzer.get_bounding_box(current)
        cell_count = int(np.count_nonzero(current))

        # Calculate density in bounding box
        if bbox[2] > 0 and bbox[3] > 0:
            bbox_area = bbox[2] * bbox[3]
            density = cell_count / bbox_area
        else:
            density = 0.0

        # Detect period
        period = PatternAnalyzer.detect_period(grid_history)

        # Classify pattern type
        is_still_life = period == 1
        is_oscillator = period > 1

        # Detect spaceship (moving pattern)
        velocity = (0.0, 0.0)
        is_spaceship = False

        if len(grid_history) >= 2:
            displacement = PatternAnalyzer.detect_displacement(
                grid_history[-2], grid_history[-1]
            )
            velocity = (float(displacement[0]), float(displacement[1]))
            is_spaceship = displacement[0] != 0 or displacement[1] != 0

        # Analyze symmetries if requested
        symmetries = []
        if check_symmetry:
            sym_types = SymmetryAnalyzer.detect_symmetries(current)
            symmetries = [s.value for s in sym_types]

        return PatternMetrics(
            bounding_box=bbox,
            cell_count=cell_count,
            density=density,
            period=period,
            is_still_life=is_still_life,
            is_oscillator=is_oscillator,
            is_spaceship=is_spaceship,
            velocity=velocity,
            symmetries=symmetries,
        )

    @staticmethod
    def find_connected_components(grid: np.ndarray) -> List[np.ndarray]:
        """Find all connected components (separate patterns).

        Args:
            grid: Grid to analyze

        Returns:
            List of component grids
        """
        height, width = grid.shape
        visited = np.zeros_like(grid, dtype=bool)
        components = []

        def flood_fill(start_y: int, start_x: int) -> Set[Tuple[int, int]]:
            """Flood fill to find connected component."""
            component = set()
            queue = deque([(start_y, start_x)])

            while queue:
                y, x = queue.popleft()

                if (
                    y < 0
                    or y >= height
                    or x < 0
                    or x >= width
                    or visited[y, x]
                    or grid[y, x] == 0
                ):
                    continue

                visited[y, x] = True
                component.add((y, x))

                # Check 8 neighbors
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        queue.append((y + dy, x + dx))

            return component

        # Find all components
        for y in range(height):
            for x in range(width):
                if grid[y, x] != 0 and not visited[y, x]:
                    component_coords = flood_fill(y, x)

                    if component_coords:
                        # Create component grid
                        min_y = min(c[0] for c in component_coords)
                        max_y = max(c[0] for c in component_coords)
                        min_x = min(c[1] for c in component_coords)
                        max_x = max(c[1] for c in component_coords)

                        comp_height = max_y - min_y + 1
                        comp_width = max_x - min_x + 1

                        component_grid = np.zeros(
                            (comp_height, comp_width), dtype=grid.dtype
                        )

                        for y, x in component_coords:
                            component_grid[y - min_y, x - min_x] = grid[y, x]

                        components.append(component_grid)

        return components

    @staticmethod
    def calculate_population_statistics(
        grid_history: List[np.ndarray],
    ) -> Dict[str, float]:
        """Calculate population statistics from history.

        Args:
            grid_history: List of grid states

        Returns:
            Dictionary with statistics
        """
        if not grid_history:
            return {}

        populations = [int(np.count_nonzero(grid)) for grid in grid_history]

        return {
            "initial_population": float(populations[0]),
            "final_population": float(populations[-1]),
            "min_population": float(min(populations)),
            "max_population": float(max(populations)),
            "mean_population": float(np.mean(populations)),
            "std_population": float(np.std(populations)),
            "population_change": float(populations[-1] - populations[0]),
        }

    @staticmethod
    def is_pattern_stable(
        grid_history: List[np.ndarray], stability_window: int = 10
    ) -> bool:
        """Check if pattern has stabilized.

        Args:
            grid_history: List of grid states
            stability_window: Number of steps to check

        Returns:
            True if pattern is stable
        """
        if len(grid_history) < stability_window:
            return False

        # Check if pattern repeats with period ≤ stability_window
        period = PatternAnalyzer.detect_period(
            grid_history[-stability_window:], max_period=stability_window
        )

        return period > 0
