"""Rendering utilities for drawing grids and applying symmetry."""

from __future__ import annotations

from typing import List, Tuple
import math

import numpy as np

from .config import CELL_COLORS


def draw_grid(
    canvas,
    grid: np.ndarray,
    cell_size: int,
    show_grid: bool,
    colors: dict[int, str] | None = None,
    grid_line_color: str = "gray",
    geometry: str = "square",
) -> None:
    """Render the automaton grid to the canvas."""

    if geometry == "hexagonal":
        _draw_hex_grid(
            canvas, grid, cell_size, show_grid, colors, grid_line_color
        )
        return

    height, width = grid.shape
    canvas.delete("all")
    scroll_region = (0, 0, width * cell_size, height * cell_size)
    canvas.configure(scrollregion=scroll_region)

    active_colors = colors if colors else CELL_COLORS
    outline = grid_line_color if show_grid else ""
    for y in range(height):
        for x in range(width):
            x1 = x * cell_size
            y1 = y * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            color = active_colors.get(int(grid[y, x]), "white")
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline=outline,
                width=1,
            )


def _draw_hex_grid(
    canvas,
    grid: np.ndarray,
    cell_size: int,
    show_grid: bool,
    colors: dict[int, str] | None,
    grid_line_color: str,
) -> None:
    """Render a hexagonal grid (pointy-topped, odd-r)."""
    height, width = grid.shape
    canvas.delete("all")

    # Calculate geometric constants
    # Assume cell_size is the "width" of the hexagon (flat to flat)
    # Radius (center to corner)
    radius = cell_size / math.sqrt(3)
    hex_height = 2 * radius

    # Spacing
    col_spacing = cell_size
    row_spacing = 1.5 * radius

    scroll_width = width * col_spacing + (cell_size / 2)
    scroll_height = height * row_spacing + (hex_height / 4)
    canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))

    active_colors = colors if colors else CELL_COLORS
    outline = grid_line_color if show_grid else ""
    width_opts = {"width": 1} if show_grid else {"width": 0}

    # Pre-calculate vertex offsets
    angles = [math.radians(30 + 60 * i) for i in range(6)]
    offsets = [(radius * math.cos(a), radius * math.sin(a)) for a in angles]

    for y in range(height):
        y_pos = y * row_spacing + radius  # +radius to center vertically

        # Odd-r offset: shift odd rows right by half width
        x_shift = (cell_size / 2) if (y % 2) else 0

        for x in range(width):
            if grid[y, x] == 0 and not show_grid:
                continue

            x_pos = (
                x * col_spacing + x_shift + (cell_size / 2)
            )  # +half width center

            # Calculate vertices
            points = []
            for dx, dy in offsets:
                points.extend([x_pos + dx, y_pos + dy])

            color = active_colors.get(int(grid[y, x]), "white")

            # Only draw dead cells if grid is shown (optimization)
            if grid[y, x] != 0 or show_grid:
                canvas.create_polygon(
                    points, fill=color, outline=outline, **width_opts
                )


def symmetry_positions(
    x: int,
    y: int,
    grid_width: int,
    grid_height: int,
    symmetry: str,
) -> List[Tuple[int, int]]:
    """Return the list of coordinates affected by the symmetry mode."""

    positions = {(x, y)}
    if symmetry in ("Horizontal", "Both"):
        positions.add((grid_width - 1 - x, y))
    if symmetry in ("Vertical", "Both"):
        positions.add((x, grid_height - 1 - y))
    if symmetry == "Both":
        positions.add((grid_width - 1 - x, grid_height - 1 - y))
    if symmetry == "Radial":
        cx, cy = grid_width // 2, grid_height // 2
        dx, dy = x - cx, y - cy
        radial = {
            (cx + dx, cy + dy),
            (cx - dx, cy - dy),
            (cx - dy, cy + dx),
            (cx + dy, cy - dx),
        }
        positions.update(radial)
    return list(positions)
