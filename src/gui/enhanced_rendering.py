"""Enhanced rendering with visual effects and optimizations.

Provides improved grid rendering, anti-aliasing, better animations,
and visual enhancements for the simulator display.
"""

from __future__ import annotations

from typing import Optional
import math

import numpy as np


class EnhancedRenderer:
    """Enhanced rendering engine with visual effects and optimizations."""

    def __init__(self, theme_colors: Optional[dict] = None) -> None:
        """Initialize enhanced renderer.

        Args:
            theme_colors: Dictionary of color definitions
        """
        self.theme_colors = theme_colors or {}
        self.last_grid: Optional[np.ndarray] = None
        self.animation_frame = 0

    def render_grid_with_effects(
        self,
        grid: np.ndarray,
        cell_size: int,
        effects: Optional[dict] = None,
    ) -> list[tuple[int, int, int, int, str, str]]:
        """Generate rendering commands with visual effects.

        Args:
            grid: Grid to render
            cell_size: Size of each cell in pixels
            effects: Dictionary of effect parameters

        Returns:
            List of (x1, y1, x2, y2, fill_color, outline_color) tuples
        """
        effects = effects or {}
        commands = []

        height, width = grid.shape

        for y in range(height):
            for x in range(width):
                cell_value = grid[y, x]
                x1 = x * cell_size
                y1 = y * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                # Determine colors
                fill_color = self._get_cell_color(cell_value, effects)
                outline_color = self._get_outline_color(cell_value, effects)

                # Apply visual effects
                if effects.get("glow", False) and cell_value > 0:
                    # Add glow effect
                    fill_color = self._apply_glow(fill_color)

                if effects.get("pulse", False) and cell_value > 0:
                    # Apply pulsing effect
                    fill_color = self._apply_pulse(fill_color, self.animation_frame)

                commands.append((x1, y1, x2, y2, fill_color, outline_color))

        self.last_grid = grid.copy()
        return commands

    def _get_cell_color(self, cell_value: int, effects: dict) -> str:
        """Get color for cell value.

        Args:
            cell_value: Cell state value
            effects: Effect parameters

        Returns:
            Hex color string
        """
        color_map = self.theme_colors.copy()

        # Check for age-based coloring
        if effects.get("age_based", False) and isinstance(cell_value, int):
            if cell_value == 0:
                return color_map.get("cell_dead", "#ffffff")

            # Map age to color (blue to red)
            max_age = effects.get("max_age", 100)
            age_ratio = min(cell_value / max_age, 1.0)

            r = int(255 * age_ratio)
            g = 0
            b = int(255 * (1.0 - age_ratio))

            return f"#{r:02x}{g:02x}{b:02x}"

        if cell_value == 0:
            return color_map.get("cell_dead", "#ffffff")
        elif cell_value == 1:
            return color_map.get("cell_alive", "#000000")
        else:
            return color_map.get(f"cell_{cell_value}", "#999999")

    def _get_outline_color(self, cell_value: int, effects: dict) -> str:
        """Get outline color for cell.

        Args:
            cell_value: Cell state value
            effects: Effect parameters

        Returns:
            Hex color string
        """
        if effects.get("show_grid", True):
            return self.theme_colors.get("grid_line", "#cccccc")
        return ""

    def _apply_glow(self, color: str) -> str:
        """Apply glow effect to color (brighten).

        Args:
            color: Base color in hex format

        Returns:
            Brightened color
        """
        # Extract RGB
        color = color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        # Brighten
        r = min(r + 60, 255)
        g = min(g + 60, 255)
        b = min(b + 60, 255)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _apply_pulse(self, color: str, frame: int) -> str:
        """Apply pulsing animation to color.

        Args:
            color: Base color in hex format
            frame: Current animation frame

        Returns:
            Modulated color
        """
        # Create pulse effect
        pulse_value = 0.5 + 0.5 * math.sin(frame * math.pi / 10)

        color = color.lstrip("#")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        # Modulate brightness
        r = int(r * pulse_value)
        g = int(g * pulse_value)
        b = int(b * pulse_value)

        return f"#{r:02x}{g:02x}{b:02x}"

    def detect_changes(
        self,
        grid: np.ndarray,
        previous_grid: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Detect which cells have changed.

        Args:
            grid: Current grid
            previous_grid: Previous grid state

        Returns:
            Boolean array indicating changed cells
        """
        if previous_grid is None or previous_grid.shape != grid.shape:
            return np.ones(grid.shape, dtype=bool)

        return grid != previous_grid

    def get_change_intensity(
        self,
        cell_value: int,
        previous_value: int,
    ) -> float:
        """Get visual intensity for changed cell.

        Args:
            cell_value: Current cell value
            previous_value: Previous cell value

        Returns:
            Intensity value (0.0 to 1.0)
        """
        if previous_value == 0 and cell_value > 0:
            return 1.0  # Birth - highest intensity
        elif previous_value > 0 and cell_value == 0:
            return 0.5  # Death - medium intensity
        else:
            return 0.0  # No change

    def next_animation_frame(self) -> None:
        """Advance animation frame counter."""
        self.animation_frame = (self.animation_frame + 1) % 100


class GridOptimizer:
    """Optimize grid rendering for performance."""

    @staticmethod
    def get_visible_cells(
        grid: np.ndarray,
        viewport: tuple[int, int, int, int],
        cell_size: int,
    ) -> np.ndarray:
        """Get only cells visible in viewport.

        Args:
            grid: Full grid
            viewport: (x1, y1, x2, y2) viewport coordinates
            cell_size: Size of each cell

        Returns:
            Indices of visible cells
        """
        x1, y1, x2, y2 = viewport

        # Convert to cell coordinates
        cell_x1 = max(0, x1 // cell_size)
        cell_y1 = max(0, y1 // cell_size)
        cell_x2 = min(grid.shape[1], (x2 // cell_size) + 1)
        cell_y2 = min(grid.shape[0], (y2 // cell_size) + 1)

        return np.s_[cell_y1:cell_y2, cell_x1:cell_x2]

    @staticmethod
    def compress_empty_regions(
        grid: np.ndarray,
        threshold: int = 10,
    ) -> list[tuple[int, int, int, int, int]]:
        """Identify rectangular regions of dead cells.

        Args:
            grid: Grid to analyze
            threshold: Minimum region size

        Returns:
            List of (x, y, width, height, value) tuples
        """
        regions = []
        height, width = grid.shape

        visited = np.zeros_like(grid, dtype=bool)

        for y in range(height):
            for x in range(width):
                if visited[y, x] or grid[y, x] != 0:
                    continue

                # Find extent of empty region along current row
                dx = 1
                while x + dx < width and grid[y, x + dx] == 0 and not visited[y, x + dx]:
                    dx += 1

                # Extend downward only while the full row-span is empty
                dy = 1
                while y + dy < height:
                    row_ok = True
                    for cx in range(x, x + dx):
                        if grid[y + dy, cx] != 0 or visited[y + dy, cx]:
                            row_ok = False
                            break
                    if not row_ok:
                        break
                    dy += 1

                if dx * dy >= threshold:
                    regions.append((x, y, dx, dy, 0))
                    visited[y:y + dy, x:x + dx] = True

        return regions


class CellAnimator:
    """Animate cell state transitions."""

    def __init__(self) -> None:
        """Initialize cell animator."""
        self.transitions: dict = {}
        self.animation_duration = 0.2  # seconds

    def add_transition(
        self,
        x: int,
        y: int,
        from_state: int,
        to_state: int,
    ) -> None:
        """Add cell state transition to animate.

        Args:
            x: Cell x coordinate
            y: Cell y coordinate
            from_state: Starting state
            to_state: Ending state
        """
        key = (x, y)
        self.transitions[key] = {
            "from": from_state,
            "to": to_state,
            "progress": 0.0,
            "start_time": 0,
        }

    def update_transitions(self, elapsed_time: float) -> dict:
        """Update animation progress.

        Args:
            elapsed_time: Time elapsed in seconds

        Returns:
            Dictionary of cell positions and animation progress
        """
        result = {}
        expired_keys = []

        for key, transition in self.transitions.items():
            progress = elapsed_time / self.animation_duration

            if progress >= 1.0:
                expired_keys.append(key)
            else:
                result[key] = progress
                transition["progress"] = progress

        # Remove completed transitions
        for key in expired_keys:
            del self.transitions[key]

        return result

    def get_transition_color(
        self,
        from_color: str,
        to_color: str,
        progress: float,
    ) -> str:
        """Interpolate between two colors.

        Args:
            from_color: Starting color in hex format
            to_color: Ending color in hex format
            progress: Transition progress (0.0 to 1.0)

        Returns:
            Interpolated color in hex format
        """
        from_color = from_color.lstrip("#")
        to_color = to_color.lstrip("#")

        r1 = int(from_color[0:2], 16)
        g1 = int(from_color[2:4], 16)
        b1 = int(from_color[4:6], 16)

        r2 = int(to_color[0:2], 16)
        g2 = int(to_color[2:4], 16)
        b2 = int(to_color[4:6], 16)

        # Ease-in-out interpolation
        eased = progress * progress * (3 - 2 * progress)

        r = int(r1 + (r2 - r1) * eased)
        g = int(g1 + (g2 - g1) * eased)
        b = int(b1 + (b2 - b1) * eased)

        return f"#{r:02x}{g:02x}{b:02x}"


def interpolate_color(
    start: str,
    end: str,
    factor: float,
) -> str:
    """Interpolate between two colors.

    Args:
        start: Starting color in hex format
        end: Ending color in hex format
        factor: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated color in hex format
    """
    start = start.lstrip("#")
    end = end.lstrip("#")

    r1 = int(start[0:2], 16)
    g1 = int(start[2:4], 16)
    b1 = int(start[4:6], 16)

    r2 = int(end[0:2], 16)
    g2 = int(end[2:4], 16)
    b2 = int(end[4:6], 16)

    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)

    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(color: str, factor: float = 0.7) -> str:
    """Darken a color.

    Args:
        color: Color in hex format
        factor: Darkening factor (0.0 to 1.0)

    Returns:
        Darkened color in hex format
    """
    color = color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)

    return f"#{r:02x}{g:02x}{b:02x}"


def lighten_color(color: str, factor: float = 0.3) -> str:
    """Lighten a color.

    Args:
        color: Color in hex format
        factor: Lightening factor (0.0 to 1.0)

    Returns:
        Lightened color in hex format
    """
    color = color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    r = min(int(r + (255 - r) * factor), 255)
    g = min(int(g + (255 - g) * factor), 255)
    b = min(int(b + (255 - b) * factor), 255)

    return f"#{r:02x}{g:02x}{b:02x}"
