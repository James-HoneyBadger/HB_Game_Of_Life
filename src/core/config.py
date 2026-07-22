"""Configuration for the simulator core."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Optional


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

    # Automaton settings
    automaton_mode: str = "Conway's Game of Life"
    birth_rule: Optional[set] = None
    survival_rule: Optional[set] = None

    # Feature flags
    enable_metrics: bool = True
    enable_cycle_detection: bool = True
    enable_complexity_tracking: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> SimulatorConfig:
        """Create config from dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "speed": self.speed,
            "cell_size": self.cell_size,
            "show_grid": self.show_grid,
            "automaton_mode": self.automaton_mode,
            "birth_rule": self.birth_rule,
            "survival_rule": self.survival_rule,
            "enable_metrics": self.enable_metrics,
            "enable_cycle_detection": self.enable_cycle_detection,
            "enable_complexity_tracking": self.enable_complexity_tracking,
        }
