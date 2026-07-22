"""Enhanced statistics for cellular automata analysis.

This module provides advanced metrics including entropy, complexity,
fractal dimension estimates, and other analytical measures.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import ndimage


class EnhancedStatistics:
    """Advanced statistical analysis for cellular automata.

    Provides various metrics for analyzing pattern complexity,
    randomness, and structural properties.
    """

    @staticmethod
    def calculate_entropy(grid: np.ndarray) -> float:
        """Calculate Shannon entropy of the grid.

        Measures the amount of information/randomness in the pattern.
        Higher entropy indicates more disorder.

        Args:
            grid: 2D numpy array

        Returns:
            Entropy value (0 to log2(num_states))
        """
        # Count state frequencies
        unique, counts = np.unique(grid, return_counts=True)
        total = grid.size

        # Calculate probabilities
        probabilities = counts / total

        # Calculate Shannon entropy
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

        return float(entropy)

    @staticmethod
    def calculate_complexity(
        grid: np.ndarray, previous_grid: Optional[np.ndarray] = None
    ) -> float:
        """Calculate pattern complexity score.

        Combines several metrics to estimate structural complexity.

        Args:
            grid: Current grid state
            previous_grid: Previous grid state for change detection

        Returns:
            Complexity score (0-1)
        """
        height, width = grid.shape
        total_cells = height * width

        # Component 1: Density (how full is the grid)
        density = np.sum(grid > 0) / total_cells

        # Component 2: Edge count (structural complexity)
        # Count neighboring pairs of different states
        edge_count = 0
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            shifted = np.roll(np.roll(grid, dy, axis=0), dx, axis=1)
            edge_count += np.sum(grid != shifted)

        edge_ratio = edge_count / (4 * total_cells)

        # Component 3: Spatial entropy (local variation)
        # Divide into blocks and measure variation
        block_size = 4
        spatial_var = 0
        for i in range(0, height - block_size, block_size):
            for j in range(0, width - block_size, block_size):
                block = grid[i : i + block_size, j : j + block_size]
                spatial_var += np.std(block)

        spatial_var /= ((height // block_size) * (width // block_size) + 1)

        # Component 4: Change rate (if previous grid available)
        change_ratio = 0.0
        if previous_grid is not None:
            changes = np.sum(grid != previous_grid)
            change_ratio = changes / total_cells

        # Combine components
        complexity = (
            0.3 * density + 0.3 * edge_ratio + 0.2 * spatial_var + 0.2 * change_ratio
        )

        return float(np.clip(complexity, 0, 1))

    @staticmethod
    def box_counting_dimension(grid: np.ndarray, max_box_size: int = 32) -> float:
        """Estimate fractal dimension using box-counting method.

        Args:
            grid: Binary grid (0/1)
            max_box_size: Maximum box size for counting

        Returns:
            Estimated fractal dimension
        """
        # Binarize grid
        binary = (grid > 0).astype(int)

        sizes = []
        counts = []

        # Try different box sizes (powers of 2)
        box_size = 1
        while box_size <= max_box_size and box_size < min(grid.shape) // 2:
            # Count boxes containing at least one live cell
            count = 0
            height, width = grid.shape

            for i in range(0, height, box_size):
                for j in range(0, width, box_size):
                    box = binary[
                        i : min(i + box_size, height),
                        j : min(j + box_size, width),
                    ]
                    if np.any(box):
                        count += 1

            if count > 0:
                sizes.append(box_size)
                counts.append(count)

            box_size *= 2

        if len(sizes) < 2:
            return 0.0

        # Fit log-log plot
        log_sizes = np.log(sizes)
        log_counts = np.log(counts)

        # Linear regression
        coeffs = np.polyfit(log_sizes, log_counts, 1)
        dimension = -coeffs[0]  # Negative slope is the dimension

        return float(dimension)

    @staticmethod
    def connected_components(grid: np.ndarray) -> tuple[int, np.ndarray]:
        """Count connected components in the grid.

        Args:
            grid: Binary grid

        Returns:
            Tuple of (num_components, labeled_array)
        """
        binary = (grid > 0).astype(int)
        labeled, num_features = ndimage.label(binary)
        return int(num_features), labeled

    @staticmethod
    def cluster_statistics(grid: np.ndarray) -> dict:
        """Analyze clusters of live cells.

        Args:
            grid: Grid to analyze

        Returns:
            Dictionary with cluster statistics
        """
        num_components, labeled = EnhancedStatistics.connected_components(grid)

        if num_components == 0:
            return {
                "num_clusters": 0,
                "avg_cluster_size": 0.0,
                "largest_cluster": 0,
                "smallest_cluster": 0,
            }

        # Calculate cluster sizes
        cluster_sizes = [
            np.sum(labeled == i) for i in range(1, num_components + 1)
        ]

        return {
            "num_clusters": num_components,
            "avg_cluster_size": float(np.mean(cluster_sizes)),
            "largest_cluster": int(np.max(cluster_sizes)),
            "smallest_cluster": int(np.min(cluster_sizes)),
        }

    @staticmethod
    def pattern_symmetry(grid: np.ndarray) -> dict:
        """Analyze pattern symmetry.

        Args:
            grid: Grid to analyze

        Returns:
            Dictionary with symmetry scores (0-1)
        """
        height, width = grid.shape

        # Horizontal symmetry
        flipped_h = np.flip(grid, axis=1)
        h_similarity = np.sum(grid == flipped_h) / grid.size

        # Vertical symmetry
        flipped_v = np.flip(grid, axis=0)
        v_similarity = np.sum(grid == flipped_v) / grid.size

        # Rotational symmetry (180 degrees)
        rotated_180 = np.rot90(grid, 2)
        r_similarity = np.sum(grid == rotated_180) / grid.size

        # Diagonal symmetry (main diagonal)
        if height == width:
            transposed = np.transpose(grid)
            d_similarity = np.sum(grid == transposed) / grid.size
        else:
            d_similarity = 0.0

        return {
            "horizontal": float(h_similarity),
            "vertical": float(v_similarity),
            "rotational_180": float(r_similarity),
            "diagonal": float(d_similarity),
        }

    @staticmethod
    def center_of_mass(grid: np.ndarray) -> tuple[float, float]:
        """Calculate center of mass of live cells.

        Args:
            grid: Grid to analyze

        Returns:
            Tuple of (x, y) coordinates
        """
        live_cells = np.argwhere(grid > 0)

        if len(live_cells) == 0:
            return (0.0, 0.0)

        # Calculate average position
        center_y = float(np.mean(live_cells[:, 0]))
        center_x = float(np.mean(live_cells[:, 1]))

        return (center_x, center_y)

    @staticmethod
    def radial_distribution(
        grid: np.ndarray, num_bins: int = 20
    ) -> tuple[np.ndarray, np.ndarray]:
        """Calculate radial distribution of cells from center of mass.

        Args:
            grid: Grid to analyze
            num_bins: Number of distance bins

        Returns:
            Tuple of (distances, densities)
        """
        center_x, center_y = EnhancedStatistics.center_of_mass(grid)

        height, width = grid.shape

        # Create distance grid from center
        y_coords, x_coords = np.ogrid[:height, :width]
        distances = np.sqrt((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2)

        max_dist = np.sqrt(width**2 + height**2) / 2
        bin_edges = np.linspace(0, max_dist, num_bins + 1)

        # Count live cells in each distance bin
        densities = []
        for i in range(num_bins):
            mask = (distances >= bin_edges[i]) & (distances < bin_edges[i + 1])
            if np.sum(mask) > 0:
                density = np.sum((grid > 0) & mask) / np.sum(mask)
            else:
                density = 0.0
            densities.append(density)

        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        return bin_centers, np.array(densities)

    @staticmethod
    def compute_all_metrics(
        grid: np.ndarray, previous_grid: Optional[np.ndarray] = None
    ) -> dict:
        """Compute all available statistical metrics.

        Args:
            grid: Current grid state
            previous_grid: Previous grid state (optional)

        Returns:
            Dictionary with all metrics
        """
        metrics = {
            "entropy": EnhancedStatistics.calculate_entropy(grid),
            "complexity": EnhancedStatistics.calculate_complexity(
                grid, previous_grid
            ),
            "fractal_dimension": EnhancedStatistics.box_counting_dimension(grid),
            "center_of_mass": EnhancedStatistics.center_of_mass(grid),
        }

        # Add cluster statistics
        metrics.update(EnhancedStatistics.cluster_statistics(grid))

        # Add symmetry scores
        symmetry = EnhancedStatistics.pattern_symmetry(grid)
        metrics["symmetry"] = symmetry

        return metrics
