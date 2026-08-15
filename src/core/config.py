"""Configuration for the simulator core."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Optional

from .boundary import BoundaryMode


@dataclass
class SimulatorConfig:
    """Configuration settings for the cellular automaton simulator.

    This separates configuration management from the GUI layer,
    making it easier to test and use in different contexts.
    """

    # pylint: disable=too-many-instance-attributes

    width: int = 100
    height: int = 100
    speed: int = 50
    cell_size: int = 8
    show_grid: bool = True
    boundary_mode: BoundaryMode = BoundaryMode.WRAP
    seed: Optional[int] = None

    # Automaton settings
    automaton_mode: str = "Conway's Game of Life"
    birth_rule: Optional[set] = None
    survival_rule: Optional[set] = None

    # Feature flags
    enable_metrics: bool = True
    enable_cycle_detection: bool = True
    max_cycle_states: int = 10000
    enable_complexity_tracking: bool = True

    def __post_init__(self) -> None:
        """Normalize enum input and validate engine-critical values."""
        if self.width < 1 or self.height < 1:
            raise ValueError("width and height must be greater than zero")
        if self.max_cycle_states < 1:
            raise ValueError("max_cycle_states must be greater than zero")
        if isinstance(self.boundary_mode, str):
            self.boundary_mode = BoundaryMode.from_string(self.boundary_mode)

    @classmethod
    def from_dict(cls, data: dict) -> SimulatorConfig:
        """Create config from dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        values = {k: v for k, v in data.items() if k in valid_keys}
        boundary = values.get("boundary_mode")
        if isinstance(boundary, str):
            values["boundary_mode"] = BoundaryMode.from_string(boundary)
        return cls(**values)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "speed": self.speed,
            "cell_size": self.cell_size,
            "show_grid": self.show_grid,
            "boundary_mode": self.boundary_mode.value,
            "seed": self.seed,
            "automaton_mode": self.automaton_mode,
            "birth_rule": self.birth_rule,
            "survival_rule": self.survival_rule,
            "enable_metrics": self.enable_metrics,
            "enable_cycle_detection": self.enable_cycle_detection,
            "max_cycle_states": self.max_cycle_states,
            "enable_complexity_tracking": self.enable_complexity_tracking,
        }
