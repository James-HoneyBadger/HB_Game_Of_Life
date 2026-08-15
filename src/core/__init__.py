"""Core automation logic separated from GUI.

This package provides a clean, testable API for cellular automaton simulation
without any GUI dependencies. It enables CLI usage and easier integration with
other tools.
"""

from .boundary import (
    BoundaryMode,
    convolve_with_boundary,
    list_boundary_modes,
    roll_with_boundary,
)
from .config import SimulatorConfig
from .simulator import Simulator
from .undo_manager import UndoManager

__all__ = [
    "BoundaryMode",
    "Simulator",
    "SimulatorConfig",
    "UndoManager",
    "convolve_with_boundary",
    "list_boundary_modes",
    "roll_with_boundary",
]
