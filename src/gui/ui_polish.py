"""UI polish and user experience enhancements.

Provides features like smooth animations, better dialogs, improved
menus, and overall visual polish.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict
import math


class AnimatedLabel(tk.Label):
    """Label with animated text and value changes."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        """Initialize animated label."""
        super().__init__(parent, **kwargs)
        self.target_value: Optional[int] = None
        self.current_value: int = 0
        self.animation_speed: float = 0.1
        self.after_id: Optional[str] = None

    def animate_to(
        self,
        target: int,
        duration_ms: int = 500,
        prefix: str = "",
        suffix: str = "",
    ) -> None:
        """Animate value change smoothly.

        Args:
            target: Target value
            duration_ms: Animation duration in milliseconds
            prefix: Text prefix
            suffix: Text suffix
        """
        if self.after_id:
            self.after_cancel(self.after_id)

        self.target_value = target
        diff = target - self.current_value
        steps = duration_ms // 50
        step_size = diff / max(steps, 1)

        self.prefix = prefix
        self.suffix = suffix
        self.step_size = step_size
        self._animate_step()

    def _animate_step(self) -> None:
        """Perform one animation step."""
        if self.target_value is None:
            return

        # Move closer to target
        if abs(self.target_value - self.current_value) > abs(self.step_size):
            self.current_value += self.step_size
        else:
            self.current_value = self.target_value
            self.target_value = None

        # Update display
        value_str = str(int(self.current_value))
        self.config(text=f"{self.prefix}{value_str}{self.suffix}")

        if self.target_value is not None:
            self.after_id = self.after(50, self._animate_step)


class GlassPanel(tk.Frame):
    """Frosted glass effect panel for dialogs and popups."""

    def __init__(
        self,
        parent: tk.Widget,
        color: str = "#ffffff",
        alpha: float = 0.95,
        **kwargs,
    ) -> None:
        """Initialize glass panel.

        Args:
            parent: Parent widget
            color: Panel color
            alpha: Alpha transparency (0.0 to 1.0)
        """
        super().__init__(parent, bg=color, **kwargs)
        self.color = color
        self.alpha = alpha
        self.relief = tk.FLAT
        self.bd = 0


class ModernDialog(tk.Toplevel):
    """Modern dialog with improved styling and transitions."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Dialog",
        width: int = 400,
        height: int = 300,
        resizable: bool = False,
    ) -> None:
        """Initialize modern dialog.

        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width
            height: Dialog height
            resizable: Whether dialog is resizable
        """
        super().__init__(parent)

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(resizable, resizable)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Create main layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Title bar
        title_bar = tk.Frame(self, bg="#0078d4", height=40)
        title_bar.grid(row=0, column=0, sticky="nsew")

        title_label = tk.Label(
            title_bar,
            text=title,
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#0078d4",
        )
        title_label.pack(padx=15, pady=10, anchor=tk.W)

        # Content area
        self.content_frame = tk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Button area
        button_frame = tk.Frame(self, bg="#f5f5f5", height=50)
        button_frame.grid(row=2, column=0, sticky="nsew")

        self.button_area = button_frame

    def add_button(
        self,
        text: str,
        command: Callable,
        style: str = "default",
    ) -> tk.Button:
        """Add button to dialog.

        Args:
            text: Button text
            command: Click callback
            style: Button style ('default', 'primary', 'danger')

        Returns:
            Button widget
        """
        color_map = {
            "default": "#e0e0e0",
            "primary": "#0078d4",
            "danger": "#d83b01",
        }
        fg_map = {
            "default": "#000000",
            "primary": "#ffffff",
            "danger": "#ffffff",
        }

        bg = color_map.get(style, color_map["default"])
        fg = fg_map.get(style, fg_map["default"])

        button = tk.Button(
            self.button_area,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            border=0,
            padx=20,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 10),
        )
        button.pack(side=tk.RIGHT, padx=5, pady=10)

        return button


class SplitView(tk.Frame):
    """Resizable split view with two panels."""

    def __init__(
        self,
        parent: tk.Widget,
        orientation: str = "horizontal",
        **kwargs,
    ) -> None:
        """Initialize split view.

        Args:
            parent: Parent widget
            orientation: 'horizontal' or 'vertical'
        """
        super().__init__(parent, **kwargs)

        self.orientation = orientation
        self.divider_pos = 0.5

        # Create panels
        if orientation == "horizontal":
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(2, weight=1)

            self.left_panel = tk.Frame(self)
            self.left_panel.grid(row=0, column=0, sticky="nsew")

            divider = tk.Frame(self, bg="#cccccc", width=2, cursor="sb_h_double_arrow")
            divider.grid(row=0, column=1, sticky="nsew")

            self.right_panel = tk.Frame(self)
            self.right_panel.grid(row=0, column=2, sticky="nsew")
        else:
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(2, weight=1)

            self.top_panel = tk.Frame(self)
            self.top_panel.grid(row=0, column=0, sticky="nsew")

            divider = tk.Frame(self, bg="#cccccc", height=2, cursor="sb_v_double_arrow")
            divider.grid(row=1, column=0, sticky="nsew")

            self.bottom_panel = tk.Frame(self)
            self.bottom_panel.grid(row=2, column=0, sticky="nsew")


class TabPanel(ttk.Notebook):
    """Enhanced tab panel with better styling."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        """Initialize tab panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)

        # Configure style
        style = ttk.Style()
        style.configure("TNotebook", font=("Segoe UI", 10))
        style.configure("TNotebook.Tab", padding=[20, 10])

    def add_tab(self, text: str, content: tk.Widget) -> None:
        """Add a tab.

        Args:
            text: Tab label
            content: Tab content widget
        """
        frame = tk.Frame(self)
        self.add(frame, text=text)

        content.pack(in_=frame, fill=tk.BOTH, expand=True)


class Badge(tk.Canvas):
    """Visual badge for notifications and counters."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        bg_color: str = "#ff0000",
        size: str = "small",
        **kwargs,
    ) -> None:
        """Initialize badge.

        Args:
            parent: Parent widget
            text: Badge text
            bg_color: Background color
            size: 'small', 'medium', 'large'
        """
        sizes = {"small": 20, "medium": 30, "large": 40}
        badge_size = sizes.get(size, sizes["small"])

        super().__init__(
            parent,
            width=badge_size,
            height=badge_size,
            bg="white",
            highlightthickness=0,
            **kwargs,
        )

        # Draw badge
        self.create_oval(
            0, 0, badge_size - 1, badge_size - 1,
            fill=bg_color,
            outline=bg_color,
        )

        # Add text
        self.create_text(
            badge_size // 2,
            badge_size // 2,
            text=text,
            fill="white",
            font=("Segoe UI", 8, "bold"),
        )


class LoadingAnimation(tk.Canvas):
    """Loading spinner animation."""

    def __init__(
        self,
        parent: tk.Widget,
        size: int = 50,
        color: str = "#0078d4",
        **kwargs,
    ) -> None:
        """Initialize loading animation.

        Args:
            parent: Parent widget
            size: Animation size in pixels
            color: Spinner color
        """
        super().__init__(
            parent,
            width=size,
            height=size,
            bg="white",
            highlightthickness=0,
            **kwargs,
        )

        self.size = size
        self.color = color
        self.rotation = 0
        self.running = False
        self.after_id: Optional[str] = None

    def start(self) -> None:
        """Start animation."""
        if not self.running:
            self.running = True
            self._update()

    def stop(self) -> None:
        """Stop animation."""
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
        self.delete("all")

    def _update(self) -> None:
        """Update animation frame."""
        if not self.running:
            return

        self.delete("all")

        center = self.size // 2
        radius = self.size // 3

        # Draw rotating lines
        for i in range(12):
            angle = math.radians(self.rotation + i * 30)
            x1 = center + radius * math.cos(angle)
            y1 = center + radius * math.sin(angle)
            x2 = center + (radius + 5) * math.cos(angle)
            y2 = center + (radius + 5) * math.sin(angle)

            self.create_line(
                x1, y1, x2, y2,
                fill=self.color,
                width=2,
            )

        self.rotation = (self.rotation + 10) % 360
        self.after_id = self.after(50, self._update)


class NotificationManager:
    """Manage notifications and alerts."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize notification manager.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.notifications: List[tk.Toplevel] = []

    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration_ms: int = 3000,
    ) -> None:
        """Show notification popup.

        Args:
            title: Notification title
            message: Notification message
            notification_type: 'info', 'success', 'warning', 'error'
            duration_ms: Display duration in milliseconds
        """
        # Create notification window
        notif = tk.Toplevel(self.parent)
        notif.wm_overrideredirect(True)
        notif.attributes("-topmost", True)

        # Color scheme
        colors = {
            "info": ("#0078d4", "#ffffff"),
            "success": ("#107c10", "#ffffff"),
            "warning": ("#ffc700", "#000000"),
            "error": ("#d83b01", "#ffffff"),
        }
        bg_color, fg_color = colors.get(notification_type, colors["info"])

        # Create content
        frame = tk.Frame(notif, bg=bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = tk.Label(
            frame,
            text=title,
            fg=fg_color,
            bg=bg_color,
            font=("Segoe UI", 10, "bold"),
        )
        title_label.pack(anchor=tk.W)

        message_label = tk.Label(
            frame,
            text=message,
            fg=fg_color,
            bg=bg_color,
            font=("Segoe UI", 9),
            wraplength=300,
            justify=tk.LEFT,
        )
        message_label.pack(anchor=tk.W, pady=5)

        # Position in corner
        self.parent.update_idletasks()
        width = 350
        height = 100
        x = self.parent.winfo_screenwidth() - width - 20
        y = self.parent.winfo_screenheight() - height - 20
        notif.geometry(f"{width}x{height}+{x}+{y}")

        # Auto close
        notif.after(duration_ms, notif.destroy)

        self.notifications.append(notif)


class MenuBar(tk.Menu):
    """Enhanced menu bar with better organization."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        """Initialize menu bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        parent.config(menu=self)

    def add_menu(
        self,
        name: str,
        items: List[Dict],
        tearoff: bool = False,
    ) -> tk.Menu:
        """Add a complete menu with items.

        Args:
            name: Menu name
            items: List of menu item dictionaries
            tearoff: Whether menu is tearoff

        Returns:
            Created menu
        """
        menu = tk.Menu(self, tearoff=tearoff)

        for item in items:
            if item.get("separator"):
                menu.add_separator()
            else:
                menu.add_command(
                    label=item["label"],
                    command=item.get("command"),
                    accelerator=item.get("accelerator", ""),
                )

        self.add_cascade(label=name, menu=menu)
        return menu


class ContextMenu:
    """Right-click context menu."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize context menu.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.menu = tk.Menu(parent, tearoff=False)
        self.parent.bind("<Button-3>", self._show)

    def add_item(
        self,
        label: str,
        command: Callable,
    ) -> None:
        """Add menu item.

        Args:
            label: Item label
            command: Click callback
        """
        self.menu.add_command(label=label, command=command)

    def add_separator(self) -> None:
        """Add separator."""
        self.menu.add_separator()

    def _show(self, event: tk.Event) -> None:
        """Show context menu."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
