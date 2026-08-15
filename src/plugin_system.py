"""Plugin system for custom cellular automata.

Allows users to add custom automata rules without modifying core code.
"""

from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

from automata import CellularAutomaton
from core.registry import ModeDescriptor, register_mode


class AutomatonPlugin(ABC):
    """Base class for automaton plugins.

    Subclass this to create custom automata that can be loaded at runtime.
    """
    api_version = 1
    capabilities: dict[str, bool] = {
        "patterns": True,
        "boundaries": True,
        "multi_state": False,
    }

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the automaton."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the automaton."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""

    @abstractmethod
    def create_automaton(self, width: int, height: int) -> CellularAutomaton:
        """Create an automaton instance.

        Args:
            width: Grid width
            height: Grid height

        Returns:
            CellularAutomaton instance
        """


class PluginManager:
    """Manages loading and registration of automaton plugins."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self.plugins: Dict[str, AutomatonPlugin] = {}
        self.plugin_paths: list[Path] = []

    def register_plugin(self, plugin: AutomatonPlugin) -> None:
        """Register a plugin.

        Args:
            plugin: AutomatonPlugin instance to register
        """
        self.validate_plugin(plugin)
        if plugin.name in self.plugins and self.plugins[plugin.name] is not plugin:
            raise ValueError(f"Plugin name already registered: {plugin.name}")
        self.plugins[plugin.name] = plugin
        register_mode(
            ModeDescriptor(
                name=plugin.name,
                description=plugin.description,
                factory=plugin.create_automaton,
                aliases=(plugin.name.lower(),),
                state_count=None,
                source="plugin",
                api_version=int(getattr(plugin, "api_version", 1)),
                capabilities=dict(getattr(plugin, "capabilities", {})),
            )
        )

    @staticmethod
    def validate_plugin(plugin: AutomatonPlugin) -> None:
        """Validate plugin metadata before registry registration."""
        if not isinstance(plugin.name, str) or not plugin.name.strip():
            raise ValueError("Plugin name must be a non-empty string")
        if not isinstance(plugin.description, str):
            raise ValueError("Plugin description must be a string")
        if not isinstance(plugin.version, str) or not plugin.version.strip():
            raise ValueError("Plugin version must be a non-empty string")
        if not isinstance(plugin.api_version, int) or plugin.api_version < 1:
            raise ValueError("Plugin api_version must be a positive integer")
        if not isinstance(plugin.capabilities, dict):
            raise ValueError("Plugin capabilities must be a dictionary")

    def load_plugins_from_directory(self, directory: str) -> int:
        """Load all plugins from a directory.

        Args:
            directory: Path to directory containing plugin modules

        Returns:
            Number of plugins loaded successfully
        """
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            return 0

        plugin_dir = plugin_dir.resolve()
        if plugin_dir in self.plugin_paths:
            return 0

        loaded_count = 0

        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    py_file.stem, py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Look for AutomatonPlugin subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, AutomatonPlugin)
                            and attr is not AutomatonPlugin
                        ):
                            try:
                                plugin_instance = attr()
                                self.register_plugin(plugin_instance)
                                loaded_count += 1
                            # pylint: disable=broad-exception-caught
                            except Exception:
                                continue
            # pylint: disable=broad-exception-caught
            except Exception:
                continue

        self.plugin_paths.append(plugin_dir)
        return loaded_count

    def get_plugin(self, name: str) -> Optional[AutomatonPlugin]:
        """Get a registered plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            AutomatonPlugin or None if not found
        """
        return self.plugins.get(name)

    def list_plugins(self) -> list[str]:
        """Get list of registered plugin names.

        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())

    def create_automaton(
        self, plugin_name: str, width: int, height: int
    ) -> Optional[CellularAutomaton]:
        """Create an automaton from a plugin.

        Args:
            plugin_name: Name of the plugin
            width: Grid width
            height: Grid height

        Returns:
            CellularAutomaton instance or None if plugin not found
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.create_automaton(width, height)
        return None
