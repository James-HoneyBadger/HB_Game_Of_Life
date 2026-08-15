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


BOUNDARY_ALIASES = {
    "wrap": [
        "wrap",
        "toroidal",
        "wrap-around",
        "wrap_around",
        "wraparound",
        "continuous",
        "loop",
        "wrapped",
        "periodic",
        "periodic-boundary",
        "periodic_boundary",
        "circular",
        "edge-wrap",
        "edge_wrap",
    ],
    "fixed": ["fixed", "fill", "dead", "zero"],
    "reflect": ["reflect", "mirror", "mirrored", "symm", "mirrormode"],
}


def list_boundary_modes() -> list[dict[str, object]]:
    """Return canonical boundary modes and the aliases accepted by the parser."""
    payload: list[dict[str, object]] = []
    for member in BoundaryMode:
        payload.append(
            {
                "name": member.value,
                "description": {
                    BoundaryMode.WRAP: "Toroidal wraparound: cells continue across opposite edges",
                    BoundaryMode.FIXED: "Cells outside the grid are treated as dead",
                    BoundaryMode.REFLECT: "Edges mirror the grid interior before continuing",
                }[member],
                "aliases": list(dict.fromkeys(BOUNDARY_ALIASES.get(member.value, []))),
                "capabilities": {
                    "cross_boundary_motion": member is BoundaryMode.WRAP,
                },
            }
        )
    return payload


class BoundaryMode(Enum):
    """Available boundary conditions.

    WRAP represents toroidal motion where cells crossing the edge reappear on
    the opposite side and continue moving normally.
    """

    WRAP = "wrap"
    FIXED = "fixed"
    REFLECT = "reflect"

    @classmethod
    def aliases(cls, mode: BoundaryMode | str | None = None) -> list[str]:
        """Return the canonical aliases for a boundary mode, or all aliases."""
        if mode is None:
            values: list[str] = []
            for member in cls:
                values.extend(cls.aliases(member.value))
            return sorted(set(values))

        if isinstance(mode, str):
            mode = cls.from_string(mode)

        return list(dict.fromkeys(BOUNDARY_ALIASES.get(mode.value, [])))

    @classmethod
    def from_string(cls, name: str) -> BoundaryMode:
        """Parse a boundary mode from its string name.

        Accepts the canonical names plus common aliases such as "toroidal",
        "wrap-around", and "continuous" to make toroidal edge motion discoverable
        and easier to configure from CLI/input settings.
        """
        lookup = {m.value: m for m in cls}
        lower = name.lower().strip()

        aliases = {
            "wrap": cls.WRAP,
            "toroidal": cls.WRAP,
            "wrap-around": cls.WRAP,
            "wrap_around": cls.WRAP,
            "wraparound": cls.WRAP,
            "continuous": cls.WRAP,
            "loop": cls.WRAP,
            "wrapped": cls.WRAP,
            "periodic": cls.WRAP,
            "periodic-boundary": cls.WRAP,
            "periodic_boundary": cls.WRAP,
            "circular": cls.WRAP,
            "edge-wrap": cls.WRAP,
            "edge_wrap": cls.WRAP,
            "fixed": cls.FIXED,
            "fill": cls.FIXED,
            "dead": cls.FIXED,
            "zero": cls.FIXED,
            "reflect": cls.REFLECT,
            "mirror": cls.REFLECT,
            "mirrormode": cls.REFLECT,
            "symm": cls.REFLECT,
            "mirrored": cls.REFLECT,
        }
        normalized_aliases = {
            key.replace("-", "").replace("_", "").replace(" ", ""): value
            for key, value in aliases.items()
        }

        if lower in lookup:
            return lookup[lower]
        normalized = lower.replace("-", "").replace("_", "").replace(" ", "")
        if normalized in normalized_aliases:
            return normalized_aliases[normalized]
        if lower in aliases:
            return aliases[lower]
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

    In WRAP mode we explicitly pad with the opposite edge so motion and
    neighbor counts continue across the boundary rather than stopping at the
    border.
    """
    if boundary == BoundaryMode.WRAP:
        padded = np.pad(grid, pad_width=1, mode="wrap")
        return signal.convolve2d(
            padded,
            kernel,
            mode="valid",
            boundary="fill",
            fillvalue=0,
        )

    if boundary == BoundaryMode.FIXED:
        padded = np.pad(grid, pad_width=1, mode="constant", constant_values=0)
        return signal.convolve2d(
            padded,
            kernel,
            mode="valid",
            boundary="fill",
            fillvalue=0,
        )

    if boundary == BoundaryMode.REFLECT:
        padded = np.pad(grid, pad_width=1, mode="reflect")
        return signal.convolve2d(
            padded,
            kernel,
            mode="valid",
            boundary="fill",
            fillvalue=0,
        )

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
