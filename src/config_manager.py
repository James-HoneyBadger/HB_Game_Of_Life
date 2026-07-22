"""Configuration management for the application.

This replaces hardcoded settings with a proper dataclass-based approach.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """Main application configuration.

    Centralizes configuration management without depending on the GUI layer.
    """

    # pylint: disable=too-many-instance-attributes

    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_title: str = "LifeGrid"

    # Grid settings
    grid_width: int = 100
    grid_height: int = 100
    grid_size_selection: str = "100x100"

    # Display settings
    cell_size: int = 8
    show_grid: bool = True
    show_stats: bool = True

    # Simulation settings
    speed: int = 50
    automaton_mode: str = "Conway's Game of Life"
    default_pattern: str = "Random Soup"

    # Advanced Simulation State
    custom_birth: str = "3"
    custom_survival: str = "23"
    draw_mode: str = "Draw"
    symmetry: str = "None"

    # Custom Dimensions
    custom_width: int = 100
    custom_height: int = 100

    # Export settings
    export_format: str = "png"
    export_quality: int = 95

    # Theme settings
    theme: str = "light"

    # Feature flags
    enable_animations: bool = True
    enable_shortcuts: bool = True
    enable_tooltips: bool = True

    # Paths
    patterns_dir: str = "patterns"
    exports_dir: str = "exports"

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> AppConfig:
        """Load configuration from file.

        Args:
            filepath: Path to config file, or use default settings.json

        Returns:
            AppConfig instance
        """
        if filepath is None:
            filepath = "settings.json"

        config_path = Path(filepath)
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                valid_keys = {f.name for f in fields(cls)}
                return cls(
                    **{
                        k: v for k, v in data.items() if k in valid_keys
                    }
                )
            except (json.JSONDecodeError, KeyError):
                return cls()

        return cls()

    def save(self, filepath: Optional[str] = None) -> None:
        """Save configuration to file.

        Args:
            filepath: Path to config file, or use default settings.json
        """
        if filepath is None:
            filepath = "settings.json"

        config_path = Path(filepath)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        """Create configuration from dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})
