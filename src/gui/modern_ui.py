"""Modern UI styling and visual enhancements for LifeGrid.

This module provides modern, polished UI components with improved
aesthetics, smooth animations, and better visual feedback.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict
import math


class ModernTheme:
    """Modern, professional color themes with enhanced aesthetics."""

    THEMES = {
        "light_pro": {
            "bg": "#f5f5f5",
            "fg": "#1a1a1a",
            "frame_bg": "#ffffff",
            "button_bg": "#0078d4",
            "button_fg": "#ffffff",
            "button_hover": "#106ebe",
            "button_active": "#005a9e",
            "grid_line": "#e0e0e0",
            "cell_alive": "#0078d4",
            "cell_dead": "#ffffff",
            "cell_young": "#64b5f6",
            "cell_old": "#ff6f00",
            "accent": "#0078d4",
            "accent_light": "#e8f4f8",
            "border": "#d0d0d0",
            "text_secondary": "#666666",
            "success": "#107c10",
            "warning": "#ffc700",
            "error": "#d83b01",
            "canvas_bg": "#f9f9f9",
        },
        "dark_pro": {
            "bg": "#1e1e1e",
            "fg": "#e0e0e0",
            "frame_bg": "#252526",
            "button_bg": "#0e639c",
            "button_fg": "#ffffff",
            "button_hover": "#1177bb",
            "button_active": "#094771",
            "grid_line": "#3e3e42",
            "cell_alive": "#4ec9b0",
            "cell_dead": "#1e1e1e",
            "cell_young": "#9cdcfe",
            "cell_old": "#ce9178",
            "accent": "#0e639c",
            "accent_light": "#1e3a4d",
            "border": "#464647",
            "text_secondary": "#999999",
            "success": "#89d185",
            "warning": "#dcdcaa",
            "error": "#f48771",
            "canvas_bg": "#252526",
        },
        "solarized_light": {
            "bg": "#fdf6e3",
            "fg": "#657b83",
            "frame_bg": "#fef5e4",
            "button_bg": "#268bd2",
            "button_fg": "#fdf6e3",
            "button_hover": "#2a7db5",
            "button_active": "#22639c",
            "grid_line": "#eee8d5",
            "cell_alive": "#268bd2",
            "cell_dead": "#fdf6e3",
            "cell_young": "#859900",
            "cell_old": "#d33682",
            "accent": "#268bd2",
            "accent_light": "#eef7f5",
            "border": "#ddd8d0",
            "text_secondary": "#93a1a1",
            "success": "#859900",
            "warning": "#b58900",
            "error": "#dc322f",
            "canvas_bg": "#fef5e4",
        },
        "solarized_dark": {
            "bg": "#002b36",
            "fg": "#839496",
            "frame_bg": "#073642",
            "button_bg": "#268bd2",
            "button_fg": "#fdf6e3",
            "button_hover": "#2a7db5",
            "button_active": "#22639c",
            "grid_line": "#094647",
            "cell_alive": "#2aa198",
            "cell_dead": "#002b36",
            "cell_young": "#859900",
            "cell_old": "#d33682",
            "accent": "#268bd2",
            "accent_light": "#0a4b4f",
            "border": "#104547",
            "text_secondary": "#586e75",
            "success": "#859900",
            "warning": "#b58900",
            "error": "#dc322f",
            "canvas_bg": "#073642",
        },
        "cyberpunk": {
            "bg": "#0a0e27",
            "fg": "#00ff88",
            "frame_bg": "#16213e",
            "button_bg": "#00ff88",
            "button_fg": "#0a0e27",
            "button_hover": "#00dd77",
            "button_active": "#00bb66",
            "grid_line": "#1a2332",
            "cell_alive": "#00ffff",
            "cell_dead": "#0a0e27",
            "cell_young": "#ff0080",
            "cell_old": "#ffff00",
            "accent": "#00ff88",
            "accent_light": "#1a3a3a",
            "border": "#2a3a50",
            "text_secondary": "#00aa66",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "error": "#ff0055",
            "canvas_bg": "#0a0e27",
        },
    }

    def __init__(self, theme_name: str = "light_pro") -> None:
        """Initialize modern theme.

        Args:
            theme_name: Name of the theme
        """
        if theme_name not in self.THEMES:
            theme_name = "light_pro"
        self.theme_name = theme_name
        self.colors = self.THEMES[theme_name].copy()

    def get_color(self, name: str) -> str:
        """Get color by name.

        Args:
            name: Color identifier

        Returns:
            Hex color value
        """
        return self.colors.get(name, "#000000")

    def available_themes(self) -> list[str]:
        """Get all available theme names."""
        return list(self.THEMES.keys())

    def switch_theme(self, theme_name: str) -> bool:
        """Switch to a different theme.

        Args:
            theme_name: Name of the theme

        Returns:
            True if theme was switched
        """
        if theme_name not in self.THEMES:
            return False
        self.theme_name = theme_name
        self.colors = self.THEMES[theme_name].copy()
        return True


class ModernButton(ttk.Button):
    """Modern button with enhanced styling and hover effects."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        command: Optional[Callable] = None,
        theme: Optional[ModernTheme] = None,
        width: int = 15,
        **kwargs,
    ) -> None:
        """Initialize modern button.

        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            theme: Modern theme instance
            width: Button width
        """
        super().__init__(parent, text=text, command=command, width=width, **kwargs)

        self.theme = theme or ModernTheme()
        self.base_color = self.theme.get_color("button_bg")
        self.hover_color = self.theme.get_color("button_hover")
        self.active_color = self.theme.get_color("button_active")

        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)

    def _on_hover(self, _event: tk.Event) -> None:
        """Handle hover effect."""
        # Note: ttk styling is limited, this is a placeholder
        pass

    def _on_leave(self, _event: tk.Event) -> None:
        """Handle leaving hover."""
        pass


class ModernLabel(tk.Label):
    """Modern label with improved typography."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        theme: Optional[ModernTheme] = None,
        size: str = "normal",
        weight: str = "normal",
        color: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize modern label.

        Args:
            parent: Parent widget
            text: Label text
            theme: Modern theme instance
            size: Font size ('small', 'normal', 'large', 'huge')
            weight: Font weight ('normal', 'bold')
            color: Text color (uses theme fg if None)
        """
        self.theme = theme or ModernTheme()

        # Font configuration
        font_sizes = {"small": 9, "normal": 10, "large": 12, "huge": 14}
        font_size = font_sizes.get(size, 10)
        font_weight = "bold" if weight == "bold" else "normal"

        # Pop font from kwargs to avoid passing it twice to super().__init__
        caller_font = kwargs.pop("font", None)
        font_family = caller_font if caller_font is not None else "Segoe UI"
        font = (font_family, font_size, font_weight)

        fg_color = color or self.theme.get_color("fg")
        bg_color = kwargs.pop("bg", self.theme.get_color("bg"))

        super().__init__(
            parent,
            text=text,
            font=font,
            fg=fg_color,
            bg=bg_color,
            **kwargs,
        )


class StatusBar(tk.Frame):
    """Modern status bar with multiple status indicators."""

    def __init__(
        self, parent: tk.Widget, theme: Optional[ModernTheme] = None
    ) -> None:
        """Initialize status bar.

        Args:
            parent: Parent widget
            theme: Modern theme instance
        """
        self.theme = theme or ModernTheme()

        super().__init__(
            parent,
            bg=self.theme.get_color("frame_bg"),
            relief=tk.SUNKEN,
            bd=1,
        )

        self.indicators: Dict[str, Dict] = {}
        self._create_indicators()

    def _create_indicators(self) -> None:
        """Create default status indicators."""
        # Separator
        sep = tk.Frame(self, bg=self.theme.get_color("border"), height=1)
        sep.pack(fill=tk.X, pady=2)

        # Main content frame
        content = tk.Frame(self, bg=self.theme.get_color("frame_bg"))
        content.pack(fill=tk.X, padx=5, pady=2)

        # Status indicators
        self.generation_label = ModernLabel(
            content, text="Generation: 0", theme=self.theme, size="small"
        )
        self.generation_label.pack(side=tk.LEFT, padx=10)

        self.population_label = ModernLabel(
            content, text="Population: 0", theme=self.theme, size="small"
        )
        self.population_label.pack(side=tk.LEFT, padx=10)

        self.status_label = ModernLabel(
            content, text="Ready", theme=self.theme, size="small",
            color=self.theme.get_color("success")
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def update_generation(self, generation: int) -> None:
        """Update generation counter."""
        self.generation_label.config(text=f"Generation: {generation}")

    def update_population(self, population: int) -> None:
        """Update population counter."""
        self.population_label.config(text=f"Population: {population}")

    def set_status(self, status: str, status_type: str = "info") -> None:
        """Set status message.

        Args:
            status: Status message
            status_type: 'info', 'success', 'warning', 'error'
        """
        color_map = {
            "info": self.theme.get_color("accent"),
            "success": self.theme.get_color("success"),
            "warning": self.theme.get_color("warning"),
            "error": self.theme.get_color("error"),
        }
        color = color_map.get(status_type, color_map["info"])
        self.status_label.config(text=status, fg=color)


class ProgressIndicator(tk.Canvas):
    """Modern animated progress indicator."""

    def __init__(
        self,
        parent: tk.Widget,
        size: int = 30,
        theme: Optional[ModernTheme] = None,
    ) -> None:
        """Initialize progress indicator.

        Args:
            parent: Parent widget
            size: Indicator size in pixels
            theme: Modern theme instance
        """
        self.theme = theme or ModernTheme()
        self.size = size
        self.rotation = 0
        self.running = False

        super().__init__(
            parent,
            width=size,
            height=size,
            bg=self.theme.get_color("frame_bg"),
            highlightthickness=0,
        )

        self.tag_configure("spinner", fill=self.theme.get_color("accent"))

    def start(self) -> None:
        """Start the progress indicator animation."""
        if not self.running:
            self.running = True
            self._animate()

    def stop(self) -> None:
        """Stop the progress indicator animation."""
        self.running = False
        self.delete("all")

    def _animate(self) -> None:
        """Animate the progress indicator."""
        if not self.running:
            return

        self.delete("all")

        # Draw spinner
        size = self.size
        center = size / 2
        radius = size / 3

        segments = 12
        for i in range(segments):
            angle = (self.rotation + i * 30) % 360
            rad = math.radians(angle)

            x1 = center + radius * math.cos(rad)
            y1 = center + radius * math.sin(rad)

            alpha = i / segments
            brightness = int(255 * alpha)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"

            self.create_oval(
                x1 - 2, y1 - 2, x1 + 2, y1 + 2,
                fill=color,
                outline=""
            )

        self.rotation = (self.rotation + 10) % 360
        self.after(50, self._animate)


class InfoPanel(tk.Frame):
    """Modern information display panel with multiple sections."""

    def __init__(
        self, parent: tk.Widget, theme: Optional[ModernTheme] = None
    ) -> None:
        """Initialize info panel.

        Args:
            parent: Parent widget
            theme: Modern theme instance
        """
        self.theme = theme or ModernTheme()

        super().__init__(
            parent,
            bg=self.theme.get_color("accent_light"),
            relief=tk.FLAT,
            bd=0,
        )

        self.info_labels: Dict[str, tk.Label] = {}

    def add_info(self, key: str, label: str, value: str = "") -> None:
        """Add information field.

        Args:
            key: Field key
            label: Display label
            value: Initial value
        """
        frame = tk.Frame(self, bg=self.theme.get_color("accent_light"))
        frame.pack(fill=tk.X, padx=10, pady=5)

        label_widget = ModernLabel(
            frame, text=f"{label}:", theme=self.theme, weight="bold"
        )
        label_widget.pack(side=tk.LEFT)

        value_widget = ModernLabel(
            frame, text=value, theme=self.theme,
            color=self.theme.get_color("accent")
        )
        value_widget.pack(side=tk.LEFT, padx=5)

        self.info_labels[key] = value_widget

    def update_info(self, key: str, value: str) -> None:
        """Update information value.

        Args:
            key: Field key
            value: New value
        """
        if key in self.info_labels:
            self.info_labels[key].config(text=value)


class AnimatedTransition:
    """Smooth animated transitions between UI states."""

    def __init__(
        self,
        widget: tk.Widget,
        duration_ms: int = 300,
        steps: int = 20,
    ) -> None:
        """Initialize transition.

        Args:
            widget: Widget to animate
            duration_ms: Total animation duration in milliseconds
            steps: Number of animation steps
        """
        self.widget = widget
        self.duration_ms = duration_ms
        self.steps = steps
        self.step_duration = duration_ms // steps
        self.current_step = 0
        self.callback: Optional[Callable[[float], None]] = None

    def start(self, callback: Callable[[float], None]) -> None:
        """Start animation.

        Args:
            callback: Function called with progress (0.0 to 1.0)
        """
        self.callback = callback
        self.current_step = 0
        self._animate()

    def _animate(self) -> None:
        """Execute animation step."""
        if self.current_step >= self.steps:
            if self.callback:
                self.callback(1.0)
            return

        progress = self.current_step / self.steps
        if self.callback:
            self.callback(progress)

        self.current_step += 1
        self.widget.after(self.step_duration, self._animate)


class TooltipEnhanced(tk.Toplevel):
    """Modern, styled tooltip with smooth appearance."""

    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        theme: Optional[ModernTheme] = None,
    ) -> None:
        """Initialize enhanced tooltip.

        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
            theme: Modern theme instance
        """
        super().__init__(widget)

        self.theme = theme or ModernTheme()
        self.text = text
        self.widget = widget

        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)

        # Create content frame
        frame = tk.Frame(
            self,
            bg=self.theme.get_color("frame_bg"),
            relief=tk.SOLID,
            bd=1,
            highlightbackground=self.theme.get_color("border"),
            highlightthickness=1,
        )
        frame.pack()

        # Add text
        label = ModernLabel(
            frame,
            text=text,
            theme=self.theme,
            size="small",
            wraplength=200,
        )
        label.pack(padx=10, pady=5)

        # Position near cursor
        self.geometry(f"+{widget.winfo_pointerx()}+{widget.winfo_pointery() - 30}")

    def show(self) -> None:
        """Display the tooltip."""
        self.deiconify()

    def hide(self) -> None:
        """Hide the tooltip."""
        self.withdraw()


def apply_modern_theme(
    root: tk.Tk, theme_name: str | ModernTheme = "light_pro"
) -> ModernTheme:
    """Apply modern theme to entire application.

    Args:
        root: Root Tkinter window
        theme_name: Theme name or ModernTheme instance

    Returns:
        ModernTheme instance
    """
    theme = theme_name if isinstance(theme_name, ModernTheme) else ModernTheme(theme_name)

    # Configure ttk styles
    style = ttk.Style()

    # Get colors
    colors = theme.colors

    # Configure button style
    style.configure(
        "TButton",
        font=("Segoe UI", 10),
        padding=5,
    )

    # Configure label style
    style.configure(
        "TLabel",
        background=colors["bg"],
        foreground=colors["fg"],
        font=("Segoe UI", 10),
    )

    # Configure frame style
    style.configure(
        "TFrame",
        background=colors["frame_bg"],
        foreground=colors["fg"],
    )

    # Configure background
    root.config(
        bg=colors["bg"],
        fg=colors["fg"],
    )

    return theme
