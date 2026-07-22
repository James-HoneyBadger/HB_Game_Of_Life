"""
Advanced visualization tools including heatmaps and symmetry analysis.

This module provides visualization utilities for analyzing patterns
and their properties.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, cast

import numpy as np


class SymmetryType(Enum):
    """Types of symmetry."""

    NONE = "none"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ROTATIONAL_90 = "rotational_90"
    ROTATIONAL_180 = "rotational_180"
    DIAGONAL = "diagonal"
    ANTIDIAGONAL = "antidiagonal"
    POINT = "point"


class HeatmapGenerator:
    """Generate heatmaps showing cell activity or age.

    This class tracks cell activity over time and generates
    visualization data for heatmaps.

    Args:
        grid_shape: Shape of the grid (height, width)
        mode: Type of heatmap ('activity', 'age', or 'births')
    """

    def __init__(self, grid_shape: Tuple[int, int], mode: str = "activity"):
        if mode not in ("activity", "age", "births"):
            raise ValueError(f"Unknown mode: {mode}")

        self.grid_shape = grid_shape
        self.mode = mode

        # Initialize tracking arrays
        if mode == "activity":
            # Count how many times each cell was alive
            self.data = np.zeros(grid_shape, dtype=np.int32)
        elif mode == "age":
            # Track how long each cell has been alive
            self.data = np.zeros(grid_shape, dtype=np.int32)
        else:  # births
            # Count how many times each cell was born
            self.data = np.zeros(grid_shape, dtype=np.int32)

        self._previous_grid: Optional[np.ndarray] = None
        self._step_count = 0

    def update(self, grid: np.ndarray) -> None:
        """Update heatmap with current grid state.

        Args:
            grid: Current grid state
        """
        if grid.shape != self.grid_shape:
            raise ValueError(
                f"Grid shape {
                    grid.shape} doesn't match {
                    self.grid_shape}"
            )

        if self.mode == "activity":
            # Increment counter for alive cells
            self.data += (grid != 0).astype(np.int32)

        elif self.mode == "age":
            # Increment age for alive cells, reset for dead cells
            alive_mask = grid != 0
            self.data[alive_mask] += 1
            self.data[~alive_mask] = 0

        elif self.mode == "births":
            # Track births (cells that were dead and are now alive)
            if self._previous_grid is not None:
                # Use separate logic to avoid Pylint confusion on precedence
                was_dead = self._previous_grid == 0
                is_alive = grid != 0
                births = was_dead & is_alive
                self.data[births] += 1
            self._previous_grid = grid.copy()

        self._step_count += 1

    def get_heatmap(
        self, normalize: bool = True, clip_max: Optional[float] = None
    ) -> np.ndarray:
        """Get the heatmap data.

        Args:
            normalize: Whether to normalize to 0-1 range
            clip_max: Optional maximum value to clip to

        Returns:
            Heatmap array
        """
        heatmap = self.data.copy().astype(np.float32)

        if clip_max is not None:
            heatmap = np.clip(heatmap, 0, clip_max)

        if normalize and heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        return heatmap

    def get_colormap_data(self, heatmap: str = "hot") -> np.ndarray:
        """Get heatmap as RGB data.

        Args:
            heatmap: Heatmap name ('hot', 'cool', 'viridis')

        Returns:
            RGB array (height, width, 3)
        """
        hmap = self.get_heatmap(normalize=True)

        if heatmap == "hot":
            # Hot colormap: black -> red -> yellow -> white
            r = np.clip(hmap * 3, 0, 1)
            g = np.clip(hmap * 3 - 1, 0, 1)
            b = np.clip(hmap * 3 - 2, 0, 1)
        elif heatmap == "cool":
            # Cool colormap: cyan -> blue -> magenta
            r = hmap
            g = 1 - hmap
            b = np.ones_like(hmap) * 1.0
        elif heatmap == "viridis":
            # Simplified viridis: purple -> green -> yellow
            r = np.clip(hmap * 2 - 0.5, 0, 1)
            g = np.clip(hmap * 1.5, 0, 1)
            b = np.clip(1 - hmap * 2, 0, 1)
        else:
            # Default grayscale
            r = g = b = hmap

        # Stack into RGB
        rgb = np.stack([r, g, b], axis=2)

        return (rgb * 255).astype(np.uint8)

    def reset(self) -> None:
        """Reset the heatmap."""
        self.data.fill(0)
        self._previous_grid = None
        self._step_count = 0

    def get_statistics(self) -> Dict[str, float]:
        """Get statistics about the heatmap.

        Returns:
            Dictionary with statistics
        """
        return {
            "steps": self._step_count,
            "min": float(self.data.min()),
            "max": float(self.data.max()),
            "mean": float(self.data.mean()),
            "median": float(np.median(self.data)),
            "std": float(self.data.std()),
        }


class SymmetryAnalyzer:
    """Analyze pattern symmetry.

    This class detects various types of symmetry in grid patterns.
    """

    @staticmethod
    def detect_symmetries(grid: np.ndarray) -> List[SymmetryType]:
        """Detect all symmetries present in a grid.

        Args:
            grid: Grid to analyze

        Returns:
            List of detected symmetry types
        """
        symmetries = []

        if SymmetryAnalyzer.has_horizontal_symmetry(grid):
            symmetries.append(SymmetryType.HORIZONTAL)

        if SymmetryAnalyzer.has_vertical_symmetry(grid):
            symmetries.append(SymmetryType.VERTICAL)

        if SymmetryAnalyzer.has_rotational_symmetry(grid, 90):
            symmetries.append(SymmetryType.ROTATIONAL_90)

        if SymmetryAnalyzer.has_rotational_symmetry(grid, 180):
            symmetries.append(SymmetryType.ROTATIONAL_180)

        if SymmetryAnalyzer.has_diagonal_symmetry(grid):
            symmetries.append(SymmetryType.DIAGONAL)

        if SymmetryAnalyzer.has_diagonal_symmetry(grid, anti=True):
            symmetries.append(SymmetryType.ANTIDIAGONAL)

        if SymmetryAnalyzer.has_point_symmetry(grid):
            symmetries.append(SymmetryType.POINT)

        if not symmetries:
            symmetries.append(SymmetryType.NONE)

        return symmetries

    @staticmethod
    def has_horizontal_symmetry(grid: np.ndarray) -> bool:
        """Check for horizontal (left-right) symmetry.

        Args:
            grid: Grid to check

        Returns:
            True if symmetric
        """
        return np.array_equal(grid, np.fliplr(grid))

    @staticmethod
    def has_vertical_symmetry(grid: np.ndarray) -> bool:
        """Check for vertical (top-bottom) symmetry.

        Args:
            grid: Grid to check

        Returns:
            True if symmetric
        """
        return np.array_equal(grid, np.flipud(grid))

    @staticmethod
    def has_rotational_symmetry(grid: np.ndarray, angle: int) -> bool:
        """Check for rotational symmetry.

        Args:
            grid: Grid to check
            angle: Rotation angle (90 or 180)

        Returns:
            True if symmetric
        """
        if angle == 90:
            rotations = 1
        elif angle == 180:
            rotations = 2
        elif angle == 270:
            rotations = 3
        else:
            raise ValueError(f"Unsupported angle: {angle}")

        rotated = np.rot90(grid, k=rotations)
        return np.array_equal(grid, rotated)

    @staticmethod
    def has_diagonal_symmetry(grid: np.ndarray, anti: bool = False) -> bool:
        """Check for diagonal symmetry.

        Args:
            grid: Grid to check (must be square)
            anti: Check antidiagonal instead of main diagonal

        Returns:
            True if symmetric
        """
        height, width = grid.shape
        if height != width:
            return False  # Can only check on square grids

        if anti:
            # Antidiagonal: flip horizontally then transpose
            transformed = np.transpose(np.fliplr(grid))
        else:
            # Main diagonal: transpose
            transformed = np.transpose(grid)

        return np.array_equal(grid, transformed)

    @staticmethod
    def has_point_symmetry(grid: np.ndarray) -> bool:
        """Check for point (180° rotational) symmetry around center.

        Args:
            grid: Grid to check

        Returns:
            True if symmetric
        """
        # Point symmetry is equivalent to 180° rotation
        return SymmetryAnalyzer.has_rotational_symmetry(grid, 180)

    @staticmethod
    def get_symmetry_score(grid: np.ndarray) -> float:
        """Calculate overall symmetry score.

        Args:
            grid: Grid to analyze

        Returns:
            Symmetry score (0-1), higher means more symmetric
        """
        symmetries = SymmetryAnalyzer.detect_symmetries(grid)

        # Remove NONE if present
        if SymmetryType.NONE in symmetries:
            return 0.0

        # Score based on number and type of symmetries
        score = 0.0
        weights = {
            SymmetryType.HORIZONTAL: 0.15,
            SymmetryType.VERTICAL: 0.15,
            SymmetryType.ROTATIONAL_90: 0.25,
            SymmetryType.ROTATIONAL_180: 0.15,
            SymmetryType.DIAGONAL: 0.15,
            SymmetryType.ANTIDIAGONAL: 0.15,
            SymmetryType.POINT: 0.15,
        }

        for sym_type in symmetries:
            score += weights.get(sym_type, 0.0)

        return min(score, 1.0)

    @staticmethod
    def apply_symmetry(
        grid: np.ndarray, symmetry_type: SymmetryType
    ) -> np.ndarray:
        """Apply a symmetry transformation to make grid symmetric.

        Args:
            grid: Grid to transform
            symmetry_type: Type of symmetry to apply

        Returns:
            Symmetric grid
        """
        if symmetry_type == SymmetryType.HORIZONTAL:
            # Make horizontally symmetric by mirroring left half to right
            width = grid.shape[1]
            mid = width // 2
            result = grid.copy()
            result[:, mid:] = np.fliplr(result[:, : mid + (width % 2)])
            return cast(np.ndarray, result)

        if symmetry_type == SymmetryType.VERTICAL:
            # Make vertically symmetric
            height = grid.shape[0]
            mid = height // 2
            result = grid.copy()
            result[mid:, :] = np.flipud(result[: mid + (height % 2), :])
            return cast(np.ndarray, result)

        if symmetry_type == SymmetryType.ROTATIONAL_180:
            # Make 180° rotationally symmetric
            rotated = np.rot90(grid, k=2)
            return cast(np.ndarray, (grid | rotated).astype(grid.dtype))

        # For other types, return original
        return cast(np.ndarray, grid.copy())
