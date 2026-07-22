"""Boundary mode support for cellular automata.

Provides different boundary conditions:
- wrap (toroidal): default, edges wrap around
- fixed (dead): cells outside the grid are dead
- reflect: edges mirror the grid interior
"""

from __future__ import annotations

from enum import Enum

import numpy as np
from scipy import signal


class BoundaryMode(Enum):
    """Available boundary conditions."""

    WRAP = "wrap"
    FIXED = "fixed"
    REFLECT = "reflect"

    @classmethod
    def from_string(cls, name: str) -> BoundaryMode:
        """Parse a boundary mode from its string name."""
        lookup = {m.value: m for m in cls}
        lower = name.lower().strip()
        if lower in lookup:
            return lookup[lower]
        raise ValueError(
            f"Unknown boundary mode '{name}'. "
            f"Choose from: {', '.join(lookup)}"
        )


# scipy boundary keyword map
_SCIPY_BOUNDARY = {
    BoundaryMode.WRAP: "wrap",
    BoundaryMode.FIXED: "fill",
    BoundaryMode.REFLECT: "symm",
}


def convolve_with_boundary(
    grid: np.ndarray,
    kernel: np.ndarray,
    boundary: BoundaryMode = BoundaryMode.WRAP,
) -> np.ndarray:
    """Convolve *grid* with *kernel* using the specified boundary mode.

    This is a drop-in replacement for
    ``scipy.signal.convolve2d(grid, kernel, mode='same', boundary='wrap')``
    that respects the desired boundary condition.

    Args:
        grid: 2-D integer grid.
        kernel: Convolution kernel (e.g. 3x3 neighbour sum).
        boundary: Boundary condition to apply.

    Returns:
        Neighbour-count array with the same shape as *grid*.
    """
    scipy_bnd = _SCIPY_BOUNDARY[boundary]
    result: np.ndarray = signal.convolve2d(
        grid,
        kernel,
        mode="same",
        boundary=scipy_bnd,
        fillvalue=0,
    )
    return result


def roll_with_boundary(
    grid: np.ndarray,
    shift: int,
    axis: int,
    boundary: BoundaryMode = BoundaryMode.WRAP,
) -> np.ndarray:
    """``np.roll`` replacement that respects boundary mode.

    For *WRAP* this is identical to ``np.roll``.
    For *FIXED* cells that roll off the edge are replaced with 0.
    For *REFLECT* the edge is mirrored before rolling.
    """
    if boundary == BoundaryMode.WRAP:
        return np.roll(grid, shift, axis=axis)  # type: ignore[return-value]

    result = np.roll(grid, shift, axis=axis)

    if boundary == BoundaryMode.FIXED:
        if axis == 0:
            if shift > 0:
                result[:shift, :] = 0
            elif shift < 0:
                result[shift:, :] = 0
        else:
            if shift > 0:
                result[:, :shift] = 0
            elif shift < 0:
                result[:, shift:] = 0

    elif boundary == BoundaryMode.REFLECT:
        if axis == 0:
            if shift > 0:
                result[:shift, :] = np.flip(
                    grid[:shift, :], axis=0
                )
            elif shift < 0:
                result[shift:, :] = np.flip(
                    grid[shift:, :], axis=0
                )
        else:
            if shift > 0:
                result[:, :shift] = np.flip(
                    grid[:, :shift], axis=1
                )
            elif shift < 0:
                result[:, shift:] = np.flip(
                    grid[:, shift:], axis=1
                )

    return result
