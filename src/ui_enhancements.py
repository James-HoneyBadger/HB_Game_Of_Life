"""UI enhancements and improvements for better user experience."""

from __future__ import annotations

from typing import Callable, Dict, Optional


class ThemeManager:
    """Manages application themes for light/dark mode support."""

    THEMES = {
        "light": {
            "bg": "#ffffff",
            "fg": "#000000",
            "button_bg": "#e0e0e0",
            "button_fg": "#000000",
            "grid_line": "#cccccc",
            "cell_alive": "#000000",
            "cell_dead": "#ffffff",
            "accent": "#2196F3",
        },
        "dark": {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "button_bg": "#333333",
            "button_fg": "#ffffff",
            "grid_line": "#444444",
            "cell_alive": "#00ff00",
            "cell_dead": "#1e1e1e",
            "accent": "#64B5F6",
        },
    }

    def __init__(self, initial_theme: str = "light") -> None:
        """Initialize theme manager.

        Args:
            initial_theme: Initial theme name
        """
        self.current_theme = initial_theme
        self._on_theme_changed: Optional[Callable[[str], None]] = None

    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme.

        Args:
            theme_name: Theme name

        Returns:
            True if theme was changed successfully
        """
        if theme_name not in self.THEMES:
            return False

        self.current_theme = theme_name
        if self._on_theme_changed:
            self._on_theme_changed(theme_name)
        return True

    def get_theme(self) -> str:
        """Get current theme name.

        Returns:
            Current theme name
        """
        return self.current_theme

    def get_colors(self) -> Dict[str, str]:
        """Get color dictionary for current theme.

        Returns:
            Dict of color names to hex values
        """
        return self.THEMES.get(self.current_theme, self.THEMES["light"]).copy()

    def set_custom_colors(self, colors: Dict[str, str]) -> None:
        """Apply a user-defined color palette as a 'custom' theme.

        The palette is merged on top of the current theme so that omitted
        keys keep their previous value.

        Args:
            colors: Dict mapping color names to hex values.
        """
        base = self.get_colors()
        base.update(colors)
        self.THEMES["custom"] = base
        self.current_theme = "custom"
        if self._on_theme_changed:
            self._on_theme_changed("custom")

    def get_color(self, color_name: str) -> Optional[str]:
        """Get a specific color.

        Args:
            color_name: Color identifier

        Returns:
            Hex color value or None
        """
        colors = self.get_colors()
        return colors.get(color_name)

    def available_themes(self) -> list[str]:
        """Get list of available themes.

        Returns:
            List of theme names
        """
        return list(self.THEMES.keys())

    def set_on_theme_changed(
        self, callback: Optional[Callable[[str], None]]
    ) -> None:
        """Set callback for theme changes.

        Args:
            callback: Function called with new theme name
        """
        self._on_theme_changed = callback


class KeyboardShortcuts:
    """Manage keyboard shortcuts for the application."""

    DEFAULT_SHORTCUTS = {
        "play_pause": "space",
        "step_forward": "s",
        "step_backward": "Left",
        "clear": "c",
        "toggle_grid": "g",
        "open": "Ctrl+O",
        "save": "Ctrl+S",
        "export": "Ctrl+E",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "quit": "Ctrl+Q",
        "help": "F1",
        "toggle_stats": "t",
    }

    def __init__(self) -> None:
        """Initialize shortcuts with defaults."""
        self.shortcuts: Dict[str, str] = self.DEFAULT_SHORTCUTS.copy()

    def get_shortcut(self, action: str) -> Optional[str]:
        """Get shortcut for an action.

        Args:
            action: Action name

        Returns:
            Keyboard shortcut or None
        """
        return self.shortcuts.get(action)

    def set_shortcut(self, action: str, shortcut: str) -> bool:
        """Set a keyboard shortcut.

        Args:
            action: Action name
            shortcut: New shortcut key combination

        Returns:
            True if set successfully
        """
        if action in self.shortcuts:
            self.shortcuts[action] = shortcut
            return True
        return False

    def reset_shortcuts(self) -> None:
        """Reset all shortcuts to defaults."""
        self.shortcuts = self.DEFAULT_SHORTCUTS.copy()

    def get_all_shortcuts(self) -> Dict[str, str]:
        """Get all shortcuts.

        Returns:
            Dict of action->shortcut mappings
        """
        return self.shortcuts.copy()


class Tooltips:
    """Manage UI tooltips and help text."""

    TOOLTIP_TEXT = {
        "start_button": "Start/Stop the simulation",
        "step_button": "Advance one generation",
        "clear_button": "Clear the grid",
        "cell_size_slider": "Adjust cell size (pixel dimension)",
        "speed_slider": "Adjust simulation speed",
        "pattern_dropdown": "Select a preset pattern",
        "mode_dropdown": "Select automaton rule set",
        "export_button": "Export current state as PNG or GIF",
        "grid_canvas": "Click to toggle cells, drag to draw",
        "stats_panel": "Live statistics and metrics",
    }

    @classmethod
    def get_tooltip(cls, element: str) -> Optional[str]:
        """Get tooltip for UI element.

        Args:
            element: Element identifier

        Returns:
            Tooltip text or None
        """
        return cls.TOOLTIP_TEXT.get(element)

    @classmethod
    def get_all_tooltips(cls) -> Dict[str, str]:
        """Get all tooltips.

        Returns:
            Dict of element->tooltip mappings
        """
        return cls.TOOLTIP_TEXT.copy()

    @classmethod
    def add_custom_tooltip(cls, element: str, text: str) -> None:
        """Add custom tooltip.

        Args:
            element: Element identifier
            text: Tooltip text
        """
        cls.TOOLTIP_TEXT[element] = text


class SpeedPresets:
    """Speed presets for quick simulation control."""

    PRESETS = {
        "slow": 20,
        "normal": 50,
        "fast": 100,
        "very_fast": 150,
    }

    @classmethod
    def get_preset(cls, name: str) -> Optional[int]:
        """Get speed value for preset.

        Args:
            name: Preset name

        Returns:
            Speed value or None
        """
        return cls.PRESETS.get(name)

    @classmethod
    def get_all_presets(cls) -> Dict[str, int]:
        """Get all presets.

        Returns:
            Dict of preset name->speed value
        """
        return cls.PRESETS.copy()

    @classmethod
    def add_preset(cls, name: str, speed: int) -> None:
        """Add custom speed preset.

        Args:
            name: Preset name
            speed: Speed value (1-255)
        """
        if 1 <= speed <= 255:
            cls.PRESETS[name] = speed
