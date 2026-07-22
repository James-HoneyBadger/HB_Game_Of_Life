"""Visual assets and icon system for enhanced UI.

Provides SVG-to-Tkinter conversion, icon generation, and visual resources.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional
import io


class IconFactory:
    """Generate icons programmatically."""

    # Icon definitions as SVG-like dictionaries
    ICONS = {
        "play": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_play_icon(c, x, y, s, col),
        },
        "pause": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_pause_icon(c, x, y, s, col),
        },
        "stop": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_stop_icon(c, x, y, s, col),
        },
        "reset": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_reset_icon(c, x, y, s, col),
        },
        "save": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_save_icon(c, x, y, s, col),
        },
        "load": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_load_icon(c, x, y, s, col),
        },
        "delete": {
            "size": 24,
            "color": "#d83b01",
            "draw": lambda c, x, y, s, col: _draw_delete_icon(c, x, y, s, col),
        },
        "settings": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_settings_icon(c, x, y, s, col),
        },
        "help": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_help_icon(c, x, y, s, col),
        },
        "info": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_info_icon(c, x, y, s, col),
        },
        "warning": {
            "size": 24,
            "color": "#ffc700",
            "draw": lambda c, x, y, s, col: _draw_warning_icon(c, x, y, s, col),
        },
        "error": {
            "size": 24,
            "color": "#d83b01",
            "draw": lambda c, x, y, s, col: _draw_error_icon(c, x, y, s, col),
        },
        "add": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_add_icon(c, x, y, s, col),
        },
        "export": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_export_icon(c, x, y, s, col),
        },
        "import": {
            "size": 24,
            "color": "#0078d4",
            "draw": lambda c, x, y, s, col: _draw_import_icon(c, x, y, s, col),
        },
    }

    @staticmethod
    def create_icon(
        icon_name: str,
        size: int = 24,
        color: Optional[str] = None,
        parent: Optional[tk.Widget] = None,
    ) -> tk.Canvas:
        """Create icon canvas.

        Args:
            icon_name: Icon name
            size: Icon size in pixels
            color: Icon color (uses default if not specified)
            parent: Parent widget (if None, temporary canvas)

        Returns:
            Canvas widget with icon
        """
        if icon_name not in IconFactory.ICONS:
            raise ValueError(f"Unknown icon: {icon_name}")

        icon_def = IconFactory.ICONS[icon_name]
        icon_color = color or icon_def["color"]

        temp_root: Optional[tk.Tk] = None
        if parent is None:
            if tk._default_root is not None:
                parent = tk._default_root
            else:
                temp_root = tk.Tk()
                temp_root.withdraw()
                parent = temp_root

        canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg="white",
            highlightthickness=0,
        )
        # Store ref so caller can clean up the temp root if needed
        canvas._icon_temp_root = temp_root  # type: ignore[attr-defined]

        draw_func = icon_def["draw"]
        draw_func(canvas, size // 2, size // 2, size // 2 - 2, icon_color)

        return canvas

    @staticmethod
    def create_icon_image(
        icon_name: str,
        size: int = 24,
        color: Optional[str] = None,
    ) -> tk.PhotoImage:
        """Create PhotoImage from icon.

        Args:
            icon_name: Icon name
            size: Icon size
            color: Icon color

        Returns:
            PhotoImage widget
        """
        temp_root: Optional[tk.Tk] = None
        try:
            canvas_parent = tk._default_root
            if canvas_parent is None:
                temp_root = tk.Tk()
                temp_root.withdraw()
                canvas_parent = temp_root

            canvas = IconFactory.create_icon(icon_name, size, color, parent=canvas_parent)
            canvas.update_idletasks()

            ps = canvas.postscript(
                colormode="color",
                x=0,
                y=0,
                width=size,
                height=size,
            )

            try:
                from PIL import Image, ImageTk
            except ImportError as exc:
                raise RuntimeError(
                    "create_icon_image requires Pillow (pip install pillow)."
                ) from exc

            image = Image.open(io.BytesIO(ps.encode("utf-8")))
            image = image.resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        finally:
            if temp_root is not None:
                temp_root.destroy()


def _draw_play_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw play icon."""
    # Triangle pointing right
    canvas.create_polygon(
        x - radius // 2, y - radius,
        x - radius // 2, y + radius,
        x + radius, y,
        fill=color,
    )


def _draw_pause_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw pause icon."""
    # Two vertical rectangles
    gap = radius // 4
    canvas.create_rectangle(
        x - radius - gap, y - radius,
        x - gap, y + radius,
        fill=color,
    )
    canvas.create_rectangle(
        x + gap, y - radius,
        x + radius + gap, y + radius,
        fill=color,
    )


def _draw_stop_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw stop icon."""
    # Square
    canvas.create_rectangle(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=color,
    )


def _draw_reset_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw reset/refresh icon."""
    # Curved arrow
    canvas.create_arc(
        x - radius, y - radius,
        x + radius, y + radius,
        start=45,
        extent=270,
        style=tk.ARC,
        outline=color,
        width=2,
    )
    # Arrow head
    canvas.create_polygon(
        x + radius - 3, y - radius + 5,
        x + radius - 8, y - radius,
        x + radius - 5, y - radius - 5,
        fill=color,
    )


def _draw_save_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw save icon."""
    # Floppy disk shape
    # Main body
    canvas.create_rectangle(
        x - radius, y - radius,
        x + radius, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Top bar
    canvas.create_rectangle(
        x - radius, y - radius,
        x + radius, y - radius + radius // 2,
        fill=color,
    )
    # Small square (label)
    canvas.create_rectangle(
        x - radius // 2, y - radius + radius // 4,
        x + radius // 2, y - radius + 2,
        outline=color,
        fill="white",
        width=1,
    )


def _draw_load_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw load/open icon."""
    # Folder shape
    # Bottom rectangle
    canvas.create_rectangle(
        x - radius, y - radius // 2,
        x + radius, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Top tab
    canvas.create_rectangle(
        x - radius, y - radius,
        x - radius // 2, y - radius // 2,
        outline=color,
        fill=color,
        width=2,
    )


def _draw_delete_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw delete/trash icon."""
    # Trash can shape
    # Handle
    canvas.create_rectangle(
        x - radius // 3, y - radius,
        x + radius // 3, y - radius + 3,
        fill=color,
    )
    # Can body
    canvas.create_polygon(
        x - radius, y - radius + 3,
        x + radius, y - radius + 3,
        x + radius - 2, y + radius,
        x - radius + 2, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Lines
    canvas.create_line(x - radius // 2, y, x - radius // 2, y + radius - 2, fill=color, width=2)
    canvas.create_line(x, y, x, y + radius - 2, fill=color, width=2)
    canvas.create_line(x + radius // 2, y, x + radius // 2, y + radius - 2, fill=color, width=2)


def _draw_settings_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw settings/gear icon."""
    # Center circle
    canvas.create_oval(
        x - radius // 3, y - radius // 3,
        x + radius // 3, y + radius // 3,
        fill=color,
    )
    # Gear teeth
    for angle in range(0, 360, 45):
        import math
        rad = math.radians(angle)
        x1 = x + radius * 0.7 * math.cos(rad)
        y1 = y + radius * 0.7 * math.sin(rad)
        x2 = x + radius * 0.9 * math.cos(rad)
        y2 = y + radius * 0.9 * math.sin(rad)
        canvas.create_line(x1, y1, x2, y2, fill=color, width=3)


def _draw_help_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw help/question mark icon."""
    # Circle
    canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        outline=color,
        width=2,
    )
    # Question mark (simplified)
    canvas.create_text(x, y - radius // 4, text="?", font=("Arial", radius), fill=color)


def _draw_info_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw info/i icon."""
    # Circle
    canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        outline=color,
        width=2,
    )
    # Letter i
    canvas.create_text(x, y, text="i", font=("Arial", int(radius * 1.5)), fill=color)


def _draw_warning_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw warning/triangle icon."""
    # Triangle pointing up
    canvas.create_polygon(
        x, y - radius,
        x + radius, y + radius,
        x - radius, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Exclamation mark
    canvas.create_text(x, y, text="!", font=("Arial", int(radius)), fill=color)


def _draw_error_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw error/X icon."""
    # Circle
    canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        outline=color,
        width=2,
    )
    # X
    offset = radius // 2
    canvas.create_line(x - offset, y - offset, x + offset, y + offset, fill=color, width=3)
    canvas.create_line(x + offset, y - offset, x - offset, y + offset, fill=color, width=3)


def _draw_add_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw add/plus icon."""
    # Vertical line
    canvas.create_line(x, y - radius, x, y + radius, fill=color, width=3)
    # Horizontal line
    canvas.create_line(x - radius, y, x + radius, y, fill=color, width=3)


def _draw_export_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw export icon."""
    # Box with arrow
    canvas.create_rectangle(
        x - radius, y - radius // 2,
        x + radius, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Arrow pointing up
    canvas.create_polygon(
        x, y - radius,
        x - radius // 3, y - radius // 4,
        x + radius // 3, y - radius // 4,
        fill=color,
    )


def _draw_import_icon(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    color: str,
) -> None:
    """Draw import icon."""
    # Box with arrow
    canvas.create_rectangle(
        x - radius, y - radius // 2,
        x + radius, y + radius,
        outline=color,
        fill="white",
        width=2,
    )
    # Arrow pointing down
    canvas.create_polygon(
        x, y + radius,
        x - radius // 3, y + radius // 4,
        x + radius // 3, y + radius // 4,
        fill=color,
    )
