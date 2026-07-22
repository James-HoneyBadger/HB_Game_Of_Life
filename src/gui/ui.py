"""Widget construction and Tk variable helpers for the GUI."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable

from .config import DEFAULT_CANVAS_HEIGHT, DEFAULT_CANVAS_WIDTH, MODE_PATTERNS


class Tooltip:
    """Simple tooltip implementation for Tkinter widgets."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tooltip_window: tk.Toplevel | None = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: tk.Event[tk.Misc]) -> None:
        """Display the tooltip near the widget."""
        if self.tooltip_window:
            return
        # Get widget position from event
        x = event.x_root + 10
        y = event.y_root + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 10),
        )
        label.pack()

    def hide_tooltip(
        self, _event: tk.Event[tk.Misc]
    ) -> None:  # pylint: disable=unused-argument
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# pylint: disable=too-many-instance-attributes
@dataclass
class TkVars:
    """Container for the Tkinter variables shared across widgets."""

    mode: tk.StringVar
    pattern: tk.StringVar
    speed: tk.IntVar
    grid_size: tk.StringVar
    custom_width: tk.IntVar
    custom_height: tk.IntVar
    cell_size: tk.IntVar
    draw_mode: tk.StringVar
    symmetry: tk.StringVar


# pylint: disable=too-many-instance-attributes
@dataclass
class Widgets:
    """References to widgets that the application interacts with later.

    Use generic `tk.Widget` for type compatibility across `tk` and `ttk`.
    """

    start_button: tk.Widget
    pattern_combo: ttk.Combobox
    pattern_help: ttk.Label
    gen_label: tk.Widget
    population_label: tk.Widget
    canvas: tk.Canvas


# pylint: disable=too-many-instance-attributes
@dataclass
class Callbacks:
    """Callback definitions for UI events."""

    switch_mode: Callable[[str], None]
    step_once: Callable[[], None]
    step_back: Callable[[], None]
    load_pattern: Callable[[], None]
    toggle_grid: Callable[[], None]
    on_canvas_click: Callable[[tk.Event[tk.Misc]], None]
    on_canvas_drag: Callable[[tk.Event[tk.Misc]], None]


def build_ui(
    root: tk.Tk,
    variables: TkVars,
    callbacks: Callbacks,
) -> Widgets:
    """Create the Tkinter widget layout and wire up callbacks."""

    _configure_style(root)
    sidebar, content = _create_layout(root)

    pattern_combo, pattern_help = _add_automaton_section(
        sidebar,
        variables,
        callbacks,
    )
    start_button, gen_label = _add_simulation_section(
        sidebar,
        variables,
        callbacks,
    )
    population_label = _add_population_section(sidebar)
    _add_drawing_section(sidebar, variables)
    canvas = _add_canvas_area(content, callbacks)

    # Prevent resizing the window so small that the sidebar vanishes.
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    req_w = min(root.winfo_reqwidth(), max(200, screen_w - 80))
    req_h = min(root.winfo_reqheight(), max(200, screen_h - 120))
    root.minsize(req_w, req_h)

    return Widgets(
        start_button=start_button,
        pattern_combo=pattern_combo,
        pattern_help=pattern_help,
        gen_label=gen_label,
        population_label=population_label,
        canvas=canvas,
    )


def _add_menubar(root: tk.Tk, _callbacks: Callbacks) -> None:
    """Add a basic menubar with Help/About."""

    menubar = tk.Menu(root)
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(
        label="About LifeGrid",
        command=lambda: None,
    )
    # Placeholder: actual About handler is implemented in app
    # here we call a dedicated method via callbacks if present
    menubar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menubar)


def _configure_style(root: tk.Tk) -> None:
    """Apply a minimal, modern theme with light cards and soft accents."""

    base_bg = "#f4f6fb"
    card_bg = "#ffffff"
    text = "#0f172a"
    muted = "#64748b"
    accent = "#0ea5e9"
    accent_active = "#38bdf8"
    accent_pressed = "#0284c7"

    root.configure(background=base_bg)

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(
        ".",
        background=base_bg,
        foreground=text,
        font=("Segoe UI", 10),
    )
    style.configure("TFrame", background=base_bg)
    style.configure("Card.TFrame", background=card_bg, padding=8)
    style.configure(
        "Sidebar.TFrame",
        background=card_bg,
        padding=8,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe",
        background=card_bg,
        relief="flat",
        padding=8,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=card_bg,
        foreground="#334155",
        font=("Segoe UI Semibold", 10),
    )
    style.configure("TLabel", background=card_bg, foreground=text)
    style.configure("Muted.TLabel", background=card_bg, foreground=muted)
    style.configure(
        "TButton",
        padding=(10, 6),
        relief="flat",
    )
    style.configure(
        "Primary.TButton",
        background=accent,
        foreground="#ffffff",
    )
    style.map(
        "Primary.TButton",
        background=[("active", accent_active), ("pressed", accent_pressed)],
        foreground=[("disabled", muted)],
    )


def _create_layout(root: tk.Tk) -> tuple[ttk.Frame, ttk.Frame]:
    """Create the shell layout and return the sidebar and content frames."""

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    shell = ttk.Frame(root, padding=10)
    shell.grid(row=0, column=0, sticky="nsew")
    shell.columnconfigure(0, weight=0, minsize=300)
    shell.columnconfigure(1, weight=1)
    shell.rowconfigure(0, weight=1)

    sidebar = ttk.Frame(
        shell,
        style="Sidebar.TFrame",
        width=280,
        padding=8,
        borderwidth=1,
        relief="solid",
    )
    sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    sidebar.grid_propagate(False)  # keep a stable visible width

    content = ttk.Frame(shell)
    content.grid(row=0, column=1, sticky="nsew")
    content.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)

    return sidebar, content


def _add_automaton_section(
    parent: ttk.Frame,
    variables: TkVars,
    callbacks: Callbacks,
) -> tuple[ttk.Combobox, ttk.Label]:
    """Build the automaton selection area and return pattern widgets."""

    mode_frame = ttk.Labelframe(
        parent,
        text="Automaton",
        style="Card.TLabelframe",
    )
    mode_frame.pack(fill=tk.X, pady=(0, 4))

    ttk.Label(mode_frame, text="Mode").pack(anchor=tk.W)
    mode_combo = ttk.Combobox(
        mode_frame,
        textvariable=variables.mode,
        state="readonly",
        values=list(MODE_PATTERNS.keys()),
    )
    mode_combo.pack(fill=tk.X, pady=(2, 6))
    Tooltip(mode_combo, "Select the type of cellular automaton to simulate")
    mode_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: callbacks.switch_mode(variables.mode.get()),
    )

    ttk.Label(mode_frame, text="Pattern").pack(anchor=tk.W)
    pattern_combo = ttk.Combobox(
        mode_frame,
        textvariable=variables.pattern,
        state="readonly",
    )
    pattern_combo.pack(fill=tk.X, pady=(2, 6))
    Tooltip(pattern_combo, "Choose a preset pattern to load")
    pattern_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: callbacks.load_pattern(),
    )

    pattern_help = ttk.Label(
        mode_frame,
        text="",
        wraplength=220,
        style="Muted.TLabel",
        justify=tk.LEFT,
    )
    pattern_help.pack(fill=tk.X, pady=(0, 2))

    return pattern_combo, pattern_help


def _add_simulation_section(
    parent: ttk.Frame,
    variables: TkVars,
    callbacks: Callbacks,
) -> tuple[ttk.Button, ttk.Label]:
    """Add simulation controls and return start button and generation label."""

    frame = ttk.Labelframe(
        parent,
        text="Simulation",
        style="Card.TLabelframe",
    )
    frame.pack(fill=tk.X, pady=(0, 4))

    toolbar = ttk.Frame(frame)
    toolbar.pack(fill=tk.X, pady=(0, 0))

    start_button = ttk.Button(
        toolbar,
        text="Start",
        command=lambda: None,
        width=10,
        style="Primary.TButton",
    )
    start_button.pack(side=tk.LEFT, padx=(0, 6))
    Tooltip(start_button, "Start or stop the simulation (Space)")

    back_button = ttk.Button(
        toolbar,
        text="Back",
        command=callbacks.step_back,
        width=7,
    )
    back_button.pack(side=tk.LEFT, padx=(0, 6))
    Tooltip(back_button, "Step backward one generation (Left Arrow)")

    step_button = ttk.Button(
        toolbar,
        text="Step",
        command=callbacks.step_once,
        width=7,
    )
    step_button.pack(side=tk.LEFT)
    Tooltip(step_button, "Advance one generation (S)")

    # Speed slider with modern styling
    speed_frame = ttk.Frame(frame)
    speed_frame.pack(fill=tk.X, pady=(4, 0))
    speed_label = ttk.Label(speed_frame, text="Speed")
    speed_label.pack(anchor=tk.W)

    speed_scale = tk.Scale(
        frame,
        from_=1,
        to=100,
        orient=tk.HORIZONTAL,
        variable=variables.speed,
        length=160,
        showvalue=False,
        bg="#ffffff",
        fg="#0ea5e9",
        highlightthickness=0,
        troughcolor="#e2e8f0",
        activebackground="#38bdf8",
    )
    speed_scale.pack(fill=tk.X, pady=(2, 0))
    Tooltip(speed_scale, "Adjust simulation speed (1 = slow, 100 = fast)")

    gen_label = ttk.Label(
        frame,
        text="Generation: 0",
        font=("Arial", 10, "bold"),
    )
    gen_label.pack(anchor=tk.W, pady=(4, 0))

    return start_button, gen_label


def _add_population_section(
    parent: ttk.Frame,
) -> ttk.Label:
    """Add a compact population summary card."""

    frame = ttk.Labelframe(
        parent,
        text="Population",
        style="Card.TLabelframe",
    )
    frame.pack(fill=tk.X, pady=(0, 4))
    label = ttk.Label(
        frame,
        text="Live: 0 | Δ: +0 | Peak: 0 | Density: 0.0%",
        wraplength=220,
        justify=tk.LEFT,
    )
    label.pack(anchor=tk.W)

    return label


def _add_drawing_section(parent: ttk.Frame, variables: TkVars) -> None:
    """Add drawing tool radio buttons and symmetry selector."""

    frame = ttk.Labelframe(
        parent,
        text="Drawing",
        style="Card.TLabelframe",
    )
    frame.pack(fill=tk.X)

    ttk.Label(frame, text="Tool", style="Muted.TLabel").pack(
        anchor=tk.W,
        pady=(0, 4),
    )

    # Tool options in a compact row
    tools_frame = ttk.Frame(frame)
    tools_frame.pack(fill=tk.X, pady=(0, 8))

    toggle_radio = ttk.Radiobutton(
        tools_frame,
        text="Toggle",
        variable=variables.draw_mode,
        value="toggle",
    )
    toggle_radio.pack(side=tk.LEFT)
    Tooltip(toggle_radio, "Click to toggle cells on/off")

    pen_radio = ttk.Radiobutton(
        tools_frame,
        text="Pen",
        variable=variables.draw_mode,
        value="pen",
    )
    pen_radio.pack(side=tk.LEFT, padx=(16, 0))
    Tooltip(pen_radio, "Click and drag to draw live cells")

    eraser_radio = ttk.Radiobutton(
        tools_frame,
        text="Eraser",
        variable=variables.draw_mode,
        value="eraser",
    )
    eraser_radio.pack(side=tk.LEFT, padx=(16, 0))
    Tooltip(eraser_radio, "Click and drag to erase cells")

    ttk.Label(frame, text="Symmetry", style="Muted.TLabel").pack(
        anchor=tk.W,
        pady=(0, 2),
    )
    symmetry_combo = ttk.Combobox(
        frame,
        textvariable=variables.symmetry,
        state="readonly",
        values=["None", "Horizontal", "Vertical", "Both", "Radial"],
    )
    symmetry_combo.pack(fill=tk.X)
    Tooltip(symmetry_combo, "Mirror drawing actions across axes")


def _add_canvas_area(parent: ttk.Frame, callbacks: Callbacks) -> tk.Canvas:
    """Create the scrollable canvas area and return the canvas widget."""

    frame = ttk.Frame(parent)
    frame.grid(row=0, column=0, sticky="nsew")

    canvas = tk.Canvas(
        frame,
        bg="white",
        width=DEFAULT_CANVAS_WIDTH,
        height=DEFAULT_CANVAS_HEIGHT,
        highlightthickness=1,
        highlightbackground="#cccccc",
    )
    h_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
    canvas.grid(row=0, column=0, sticky=tk.NSEW)
    h_scroll.grid(row=1, column=0, sticky=tk.EW, pady=(4, 0))
    v_scroll.grid(row=0, column=1, sticky=tk.NS, padx=(4, 0))

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    canvas.bind("<Button-1>", callbacks.on_canvas_click)
    canvas.bind("<B1-Motion>", callbacks.on_canvas_drag)

    return canvas
