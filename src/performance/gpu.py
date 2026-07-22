"""GPU-accelerated grid computation with automatic fallback.

Uses CuPy as a drop-in NumPy replacement when a CUDA GPU is available.
Falls back transparently to NumPy on CPU-only machines.

Usage:
    from performance.gpu import xp, to_numpy, is_gpu_available
    grid = xp.zeros((100, 100), dtype=int)
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import cupy as cp  # type: ignore[import-untyped]

    _GPU_AVAILABLE = True
except ImportError:
    cp = None
    _GPU_AVAILABLE = False


def is_gpu_available() -> bool:
    """Return True when CuPy + CUDA are functional."""
    if not _GPU_AVAILABLE:
        return False
    try:
        cp.array([1])  # quick smoke test
        return True
    except (ImportError, RuntimeError):  # pragma: no cover
        return False


# Module-level array backend.  Import ``xp`` and use it like ``np``.
xp: Any = cp if is_gpu_available() else np


def to_numpy(arr: Any) -> np.ndarray:
    """Ensure *arr* is a host-side NumPy array (no-op if already)."""
    if _GPU_AVAILABLE and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)  # type: ignore[no-any-return]
    return np.asarray(arr)


def to_device(arr: np.ndarray) -> Any:
    """Move *arr* to the GPU if available, otherwise return as-is."""
    if is_gpu_available():
        return cp.asarray(arr)
    return arr


class GPUSimulator:
    """Thin wrapper that accelerates a step function on the GPU.

    This is *not* a full automaton — it accelerates the neighbour sum
    and rule application for life-like automata (B/S notation).
    """

    def __init__(
        self,
        grid: np.ndarray,
        birth: set[int],
        survival: set[int],
    ) -> None:
        self._birth = birth
        self._survival = survival
        self.grid = to_device(grid)
        self._kernel = xp.array(
            [[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=int
        )

    def step(self) -> None:
        """Advance one generation using the GPU (or CPU fallback)."""
        # Pad + manual convolution (CuPy has no convolve2d)
        padded = xp.pad(self.grid, 1, mode="wrap")
        neighbors = xp.zeros_like(self.grid)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue
                neighbors += padded[
                    1 + dy : 1 + dy + self.grid.shape[0],
                    1 + dx : 1 + dx + self.grid.shape[1],
                ]

        birth_mask = xp.zeros_like(self.grid, dtype=bool)
        for n in self._birth:
            birth_mask |= neighbors == n

        surv_mask = xp.zeros_like(self.grid, dtype=bool)
        for n in self._survival:
            surv_mask |= neighbors == n

        born = (self.grid == 0) & birth_mask
        survived = (self.grid == 1) & surv_mask
        self.grid = (born | survived).astype(int)

    def get_grid(self) -> np.ndarray:
        """Return the grid as a NumPy array."""
        return to_numpy(self.grid)
