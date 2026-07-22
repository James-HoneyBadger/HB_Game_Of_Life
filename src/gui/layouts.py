"""Layout and composition enhancements for better UI organization.

Provides responsive layouts, grid management, and visual composition tools.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, List, Dict, Tuple


class ResponsiveFrame(tk.Frame):
    """Frame that responds to window resizing."""

    def __init__(
        self,
        parent: tk.Widget,
        min_width: int = 100,
        min_height: int = 100,
        **kwargs,
    ) -> None:
        """Initialize responsive frame.

        Args:
            parent: Parent widget
            min_width: Minimum width
            min_height: Minimum height
        """
        super().__init__(parent, **kwargs)

        self.min_width = min_width
        self.min_height = min_height
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event: tk.Event) -> None:
        """Handle resize event."""
        # Can override in subclasses for custom behavior
        pass


class GridLayout(tk.Frame):
    """Organized grid layout for consistent spacing."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: int = 3,
        padding: int = 10,
        **kwargs,
    ) -> None:
        """Initialize grid layout.

        Args:
            parent: Parent widget
            columns: Number of columns
            padding: Spacing between items
        """
        super().__init__(parent, **kwargs)

        self.columns = columns
        self.padding = padding
        self.row = 0
        self.col = 0
        self.widgets: List[tk.Widget] = []

    def add_item(
        self,
        widget: tk.Widget,
        colspan: int = 1,
        sticky: str = "ew",
    ) -> tk.Widget:
        """Add item to grid.

        Args:
            widget: Widget to add
            colspan: Column span
            sticky: Grid sticky option

        Returns:
            Added widget
        """
        widget.grid(
            row=self.row,
            column=self.col,
            columnspan=colspan,
            padx=self.padding,
            pady=self.padding,
            sticky=sticky,
        )

        self.widgets.append(widget)
        self.col += colspan

        if self.col >= self.columns:
            self.col = 0
            self.row += 1

        return widget

    def add_row(self, *widgets: tk.Widget) -> None:
        """Add a full row of widgets.

        Args:
            *widgets: Widgets for the row
        """
        for widget in widgets:
            self.add_item(widget)


class CardPanel(tk.Frame):
    """Card-like container with shadow effect."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "",
        bg_color: str = "#ffffff",
        shadow: bool = True,
        **kwargs,
    ) -> None:
        """Initialize card panel.

        Args:
            parent: Parent widget
            title: Card title
            bg_color: Background color
            shadow: Whether to show shadow effect
        """
        super().__init__(parent, bg=bg_color, relief=tk.FLAT, **kwargs)

        self.bg_color = bg_color
        self.shadow = shadow

        # Border effect
        if shadow:
            self.configure(bd=1, relief=tk.SOLID, bg="#e0e0e0")

        # Title if provided
        if title:
            title_frame = tk.Frame(self, bg="#f5f5f5")
            title_frame.pack(fill=tk.X, padx=1, pady=1)

            title_label = tk.Label(
                title_frame,
                text=title,
                font=("Segoe UI", 10, "bold"),
                bg="#f5f5f5",
            )
            title_label.pack(padx=10, pady=5)

        # Content area
        self.content_frame = tk.Frame(self, bg=bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)


class SidePanel(tk.Frame):
    """Collapsible side panel for controls."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Panel",
        width: int = 250,
        **kwargs,
    ) -> None:
        """Initialize side panel.

        Args:
            parent: Parent widget
            title: Panel title
            width: Panel width
        """
        super().__init__(parent, **kwargs)

        self.title = title
        self.width = width
        self.expanded = True

        # Header
        header = tk.Frame(self, bg="#0078d4", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text=title,
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#0078d4",
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=8)

        toggle_btn = tk.Button(
            header,
            text="−",
            command=self.toggle,
            bg="#0078d4",
            fg="#ffffff",
            border=0,
            width=3,
            font=("Segoe UI", 10),
        )
        toggle_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.toggle_btn = toggle_btn

        # Content area
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def toggle(self) -> None:
        """Toggle panel expansion."""
        if self.expanded:
            self.content_frame.pack_forget()
            self.toggle_btn.config(text="+")
        else:
            self.content_frame.pack(fill=tk.BOTH, expand=True)
            self.toggle_btn.config(text="−")

        self.expanded = not self.expanded


class TabbedPanel(tk.Frame):
    """Modern tabbed interface."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        """Initialize tabbed panel."""
        super().__init__(parent, **kwargs)

        self.tabs: Dict[str, Tuple[tk.Button, tk.Frame]] = {}
        self.active_tab: Optional[str] = None

        # Tab bar
        self.tab_bar = tk.Frame(self, bg="#e0e0e0", height=35)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        # Content area
        self.content_frame = tk.Frame(self, bg="#ffffff")
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def add_tab(self, name: str) -> tk.Frame:
        """Add a tab.

        Args:
            name: Tab name

        Returns:
            Tab content frame
        """
        # Create tab button
        tab_btn = tk.Button(
            self.tab_bar,
            text=name,
            command=lambda: self.select_tab(name),
            bg="#e0e0e0",
            fg="#000000",
            border=0,
            padx=15,
            pady=8,
            font=("Segoe UI", 10),
        )
        tab_btn.pack(side=tk.LEFT)

        # Create tab content
        content = tk.Frame(self.content_frame, bg="#ffffff")

        self.tabs[name] = (tab_btn, content)

        if self.active_tab is None:
            self.select_tab(name)

        return content

    def select_tab(self, name: str) -> None:
        """Select a tab.

        Args:
            name: Tab name
        """
        # Deselect previous
        if self.active_tab and self.active_tab in self.tabs:
            btn, content = self.tabs[self.active_tab]
            btn.config(bg="#e0e0e0", fg="#000000")
            content.pack_forget()

        # Select new
        if name in self.tabs:
            btn, content = self.tabs[name]
            btn.config(bg="#0078d4", fg="#ffffff")
            content.pack(fill=tk.BOTH, expand=True)
            self.active_tab = name


class ToolBar(tk.Frame):
    """Modern toolbar with grouping."""

    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str = "#f5f5f5",
        **kwargs,
    ) -> None:
        """Initialize toolbar.

        Args:
            parent: Parent widget
            bg_color: Toolbar background color
        """
        super().__init__(parent, bg=bg_color, height=50, **kwargs)

        self.bg_color = bg_color
        self.pack_propagate(False)
        self.groups: Dict[str, tk.Frame] = {}

    def add_group(self, name: str) -> tk.Frame:
        """Add toolbar group.

        Args:
            name: Group name

        Returns:
            Group frame
        """
        group = tk.Frame(self, bg=self.bg_color)
        group.pack(side=tk.LEFT, padx=5, pady=8)

        self.groups[name] = group
        return group

    def add_button(
        self,
        group: str,
        text: str,
        command,
        icon: Optional[str] = None,
    ) -> tk.Button:
        """Add button to group.

        Args:
            group: Group name
            text: Button text
            command: Click callback
            icon: Icon name

        Returns:
            Button widget
        """
        if group not in self.groups:
            group_frame = self.add_group(group)
        else:
            group_frame = self.groups[group]

        btn = tk.Button(
            group_frame,
            text=text,
            command=command,
            bg="#e0e0e0",
            border=0,
            padx=10,
            pady=5,
            cursor="hand2",
            font=("Segoe UI", 9),
        )
        btn.pack(side=tk.LEFT, padx=2)

        return btn

    def add_separator(self) -> None:
        """Add vertical separator."""
        separator = tk.Frame(self, bg="#cccccc", width=1)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)


class StatusBar(tk.Frame):
    """Status bar with multiple sections."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        """Initialize status bar."""
        super().__init__(parent, bg="#f5f5f5", height=25, **kwargs)

        self.pack_propagate(False)
        self.sections: Dict[str, tk.Label] = {}

    def add_section(
        self,
        name: str,
        width: int = 100,
        relief: str = tk.SUNKEN,
    ) -> tk.Label:
        """Add status section.

        Args:
            name: Section name
            width: Section width
            relief: Section relief style

        Returns:
            Section label
        """
        section = tk.Label(
            self,
            text="",
            width=width,
            relief=relief,
            bg="#f5f5f5",
            font=("Segoe UI", 9),
        )
        section.pack(side=tk.LEFT, padx=1, pady=1, fill=tk.BOTH, expand=True)

        self.sections[name] = section
        return section

    def set_text(self, name: str, text: str) -> None:
        """Set section text.

        Args:
            name: Section name
            text: Text to display
        """
        if name in self.sections:
            self.sections[name].config(text=text)


class Spacer(tk.Frame):
    """Flexible spacer for layout."""

    def __init__(
        self,
        parent: tk.Widget,
        direction: str = "v",
        height: int = 10,
        width: int = 10,
        **kwargs,
    ) -> None:
        """Initialize spacer.

        Args:
            parent: Parent widget
            direction: 'v' for vertical, 'h' for horizontal
            height: Height in pixels
            width: Width in pixels
        """
        super().__init__(parent, bg="white", **kwargs)

        if direction == "v":
            self.pack(fill=tk.Y, expand=True)
            self.config(height=height)
        else:
            self.pack(fill=tk.X, expand=True)
            self.config(width=width)

        self.pack_propagate(False)


class DividerLine(tk.Frame):
    """Visual divider line."""

    def __init__(
        self,
        parent: tk.Widget,
        orientation: str = "horizontal",
        color: str = "#e0e0e0",
        width: int = 1,
        **kwargs,
    ) -> None:
        """Initialize divider.

        Args:
            parent: Parent widget
            orientation: 'horizontal' or 'vertical'
            color: Line color
            width: Line width
        """
        super().__init__(parent, bg=color, **kwargs)

        if orientation == "horizontal":
            self.pack(fill=tk.X, pady=5)
            self.config(height=width)
            self.pack_propagate(False)
        else:
            self.pack(fill=tk.Y, padx=5)
            self.config(width=width)
            self.pack_propagate(False)
