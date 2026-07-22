# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes, too-many-public-methods
# pylint: disable=too-many-locals, too-many-statements

"""Refactored GUI application composed of focused helper modules."""

from __future__ import annotations

import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np

from advanced.rle_format import RLEParser
from core.utils import place_pattern_centered
from automata import LifeLikeAutomaton, HexagonalGameOfLife
from config_manager import AppConfig
from patterns import get_pattern_description, PATTERN_DATA
from plugin_system import PluginManager
from ui_enhancements import ThemeManager
from version import __version__ as LIFEGRID_VERSION

from .config import (
    DEFAULT_CUSTOM_BIRTH,
    DEFAULT_CUSTOM_SURVIVAL,
    EXPORT_COLOR_MAP,
    MAX_CELL_SIZE,
    MAX_GRID_SIZE,
    MIN_CELL_SIZE,
    MIN_GRID_SIZE,
    MODE_FACTORIES,
    MODE_PATTERNS,
    CELL_COLORS,
)
from .rendering import draw_grid, symmetry_positions
from .state import SimulationState
from .tools import ToolManager, Stamp
from .ui import Callbacks, TkVars, Widgets, build_ui
from .new_features import (
    GenerationTimeline,
    PopulationGraph,
    BreakpointManager,
    BreakpointDialog,
    RuleExplorer,
    CommandPalette,
    ThemeEditorDialog,
    PatternShapeSearch,
)
from core.boundary import BoundaryMode

try:
    from PIL import Image as PILImage

    PIL_AVAILABLE = True
except ImportError:
    PILImage = None  # type: ignore[assignment]
    PIL_AVAILABLE = False


def _nearest_resample_filter() -> object | None:
    """Return the Pillow nearest-neighbour filter if available."""

    if not (PIL_AVAILABLE and PILImage):
        return None
    resampling = getattr(PILImage, "Resampling", PILImage)
    return getattr(resampling, "NEAREST", None)


class AutomatonApp:
    """High-level GUI orchestrator for the cellular automaton simulator."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("LifeGrid")

        self.theme_manager = ThemeManager()
        self.config = AppConfig.load("settings.json")

        # Load saved theme preference
        self.theme_manager.set_theme(self.config.theme)

        self.state = SimulationState()

        # Initialize Plugin System
        self.plugin_manager = PluginManager()
        self._load_plugins()

        self.custom_birth = set(DEFAULT_CUSTOM_BIRTH)
        self.custom_survival = set(DEFAULT_CUSTOM_SURVIVAL)

        # Load custom rule if present in config
        if self.config.custom_birth:
            self.custom_birth_text = self.config.custom_birth
        else:
            self.custom_birth_text = "".join(
                str(n) for n in sorted(self.custom_birth)
            )

        if self.config.custom_survival:
            self.custom_survival_text = self.config.custom_survival
        else:
            self.custom_survival_text = "".join(
                str(n) for n in sorted(self.custom_survival)
            )

        self.tk_vars: TkVars = self._create_variables()
        self.state.cell_size = self.tk_vars.cell_size.get()
        callbacks = Callbacks(
            switch_mode=self.switch_mode,
            step_once=self.step_once,
            step_back=self.step_back,
            load_pattern=self.load_pattern_handler,
            toggle_grid=self.toggle_grid,
            on_canvas_click=self.on_canvas_click,
            on_canvas_drag=self.on_canvas_drag,
        )
        self.widgets: Widgets = build_ui(
            root=self.root,
            variables=self.tk_vars,
            callbacks=callbacks,
        )
        self.widgets.start_button.configure(  # type: ignore[call-arg]
            command=self.toggle_simulation
        )

        # Apply theme
        self._apply_theme_colors()

        self.state.show_grid = self.config.show_grid

        self.tool_manager = ToolManager()
        self._configure_bindings()
        self.switch_mode(self.tk_vars.mode.get())
        self._update_widgets_enabled_state()
        self._update_display()

        # -- New feature initialization --
        self.boundary_mode = BoundaryMode.WRAP
        self.breakpoint_manager = BreakpointManager()

        # Command palette
        self.command_palette = CommandPalette(self.root)
        self._register_palette_commands()

        # Timeline scrubber (below canvas area inside content frame)
        # canvas → scroll_frame → content
        _canvas_parent = self.widgets.canvas.master
        assert _canvas_parent is not None
        content_frame = _canvas_parent.master or self.root
        self._timeline = GenerationTimeline(
            content_frame, on_seek=self._seek_generation,
        )
        self._timeline.grid(
            row=1, column=0, sticky="ew", padx=4, pady=(4, 0),
        )

        # Population graph (below timeline in content frame)
        self._pop_graph = PopulationGraph(
            content_frame, width=280, height=90,
        )
        self._pop_graph.grid(
            row=2, column=0, sticky="ew", padx=4, pady=(4, 4),
        )

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Menubar
        self._install_menubar()

    def _create_tools_menu(self, parent_menu: tk.Menu) -> None:
        """Create the Tools menu with available stamps."""
        tools_menu = tk.Menu(parent_menu, tearoff=0)

        tools_menu.add_command(
            label="Pencil (Draw Individual Cells)",
            command=self.tool_manager.set_pencil,
        )
        tools_menu.add_command(
            label="Eraser (Clear Individual Cells)",
            command=self.tool_manager.set_eraser,
        )
        tools_menu.add_command(
            label="Selection Box",
            command=self.tool_manager.set_selection,
        )
        tools_menu.add_separator()

        # Add stamps from loaded patterns
        stamps_menu = tk.Menu(tools_menu, tearoff=0)

        # We'll use Conway patterns for generic stamping for now
        # Ideally this would filter by current mode
        cats = PATTERN_DATA.get("Conway's Game of Life", {})
        count = 0
        for name, (points, desc) in cats.items():
            if len(points) < 50:  # Limit to smaller stamps
                stamp = Stamp(name, points, desc)
                stamps_menu.add_command(
                    label=name,
                    command=lambda s=stamp: self.tool_manager.set_stamp(s),  # type: ignore[misc]
                )
                count += 1
                if count >= 15:
                    break  # Don't overwhelm the menu

        tools_menu.add_cascade(label="Stamps", menu=stamps_menu)
        parent_menu.add_cascade(label="Tools", menu=tools_menu)

    def set_app_theme(self, theme_name: str) -> None:
        """Switch application theme."""
        if self.theme_manager.set_theme(theme_name):
            self.config.theme = theme_name
            self._apply_theme_colors()
            self._update_display()

    def _apply_theme_colors(self) -> None:
        """Apply current theme colors to widgets."""
        colors = self.theme_manager.get_colors()
        bg = colors["bg"]
        fg = colors["fg"]
        btn_bg = colors["button_bg"]
        btn_fg = colors["button_fg"]

        style = ttk.Style(self.root)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=btn_bg, foreground=btn_fg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TRadiobutton", background=bg, foreground=fg)

        self.root.configure(bg=bg)
        if self.widgets.canvas:
            self.widgets.canvas.configure(bg=colors["cell_dead"])

    def load_rle_pattern(self) -> None:
        """Load a pattern from an RLE file."""
        filename = filedialog.askopenfilename(
            title="Import RLE Pattern",
            filetypes=[("RLE Files", "*.rle"), ("All Files", "*.*")],
        )
        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            pattern, _ = RLEParser.parse(content)

            # Apply to current grid centered
            automaton = self.state.current_automaton
            if not automaton:
                return

            current_grid = automaton.get_grid()

            # Reset grid
            current_grid[:] = 0

            # Center the pattern
            place_pattern_centered(current_grid, pattern)

            automaton.grid = (
                current_grid  # Some automata might need explicit set
            )

            self._update_display()
            messagebox.showinfo("Success", "RLE pattern loaded successfully.")

        except Exception as e:  # pylint: disable=broad-exception-caught
            messagebox.showerror("Error", f"Failed to load RLE file:\n{e}")

    def _on_close(self) -> None:
        """Save settings and close the application."""
        self._save_settings()
        self.root.destroy()

    def _install_menubar(self) -> None:
        """Install the main application menubar."""

        def show_about() -> None:
            message = (
                f"LifeGrid v{LIFEGRID_VERSION}\n\n"
                "Interactive cellular automata workbench.\n"
                "Copyright (c) 2026 Honey Badger Universe\n\n"
                "Repo: https://github.com/James-HoneyBadger/LifeGrid\n"
            )
            messagebox.showinfo("About LifeGrid", message)

        def show_shortcuts() -> None:
            message = (
                "Keyboard shortcuts:\n\n"
                "Space       — Start/Stop\n"
                "S           — Step Forward\n"
                "Left Arrow  — Step Back\n"
                "C           — Clear Grid\n"
                "G           — Toggle Grid Lines\n"
                "D           — Toggle Dark/Light Theme\n"
                "R           — Rule Explorer\n"
                "B           — Breakpoints\n"
                "Ctrl+Z      — Undo\n"
                "Ctrl+Y      — Redo\n"
                "Ctrl+C      — Copy Selection\n"
                "Ctrl+X      — Cut Selection\n"
                "Ctrl+V      — Paste Selection\n"
                "Ctrl+Shift+P — Command Palette\n"
            )
            messagebox.showinfo("Shortcuts", message)

        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Pattern…", command=self.save_pattern)
        file_menu.add_command(
            label="Load Pattern…",
            command=self.load_saved_pattern,
        )
        file_menu.add_command(
            label="Import RLE…",
            command=self.load_rle_pattern,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Export Metrics (CSV)…",
            command=self.export_metrics,
        )
        if PIL_AVAILABLE:
            file_menu.add_command(label="Export PNG…", command=self.export_png)
        else:
            file_menu.add_command(label="Export PNG…", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(
            label="Undo", accelerator="Ctrl+Z", command=self.undo_action
        )
        edit_menu.add_command(
            label="Redo", accelerator="Ctrl+Y", command=self.redo_action
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Copy", accelerator="Ctrl+C", command=self.copy_selection
        )
        edit_menu.add_command(
            label="Cut", accelerator="Ctrl+X", command=self.cut_selection
        )
        edit_menu.add_command(
            label="Paste", accelerator="Ctrl+V", command=self.paste_selection
        )
        menubar.add_cascade(label="Edit", menu=edit_menu)

        sim_menu = tk.Menu(menubar, tearoff=0)
        # Keep vital play/step controls in the sidebar to avoid redundancy.
        sim_menu.add_command(label="Reset", command=self.reset_simulation)
        sim_menu.add_command(label="Clear", command=self.clear_grid)
        sim_menu.add_separator()
        sim_menu.add_command(
            label="Rule Explorer…",
            accelerator="R",
            command=self.open_rule_explorer,
        )
        sim_menu.add_command(
            label="Breakpoints…",
            accelerator="B",
            command=self.open_breakpoints_dialog,
        )
        sim_menu.add_command(
            label="Pattern Shape Search…",
            command=self.open_pattern_shape_search,
        )
        sim_menu.add_separator()
        boundary_menu = tk.Menu(sim_menu, tearoff=0)
        boundary_menu.add_command(
            label="Wrap (toroidal)",
            command=lambda: self._set_boundary("wrap"),
        )
        boundary_menu.add_command(
            label="Fixed (dead edges)",
            command=lambda: self._set_boundary("fixed"),
        )
        boundary_menu.add_command(
            label="Reflect (mirror)",
            command=lambda: self._set_boundary("reflect"),
        )
        sim_menu.add_cascade(label="Boundary Mode", menu=boundary_menu)
        menubar.add_cascade(label="Simulation", menu=sim_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(
            label="Grid & View Settings…",
            command=self.open_simulation_settings,
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Custom Rules…",
            command=self.open_custom_rules_dialog,
        )
        presets_menu = tk.Menu(settings_menu, tearoff=0)
        presets_menu.add_command(
            label="Conway (B3/S23)",
            command=lambda: self.apply_rule_preset("3", "23"),
        )
        presets_menu.add_command(
            label="HighLife (B36/S23)",
            command=lambda: self.apply_rule_preset("36", "23"),
        )
        presets_menu.add_command(
            label="Seeds (B2/S∅)",
            command=lambda: self.apply_rule_preset("2", ""),
        )
        presets_menu.add_command(
            label="Life (B3/S0123456789)",
            command=lambda: self.apply_rule_preset("3", "0123456789"),
        )
        settings_menu.add_cascade(label="Rule Presets", menu=presets_menu)
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Toggle Grid",
            command=self.toggle_grid,
        )

        settings_menu.add_separator()
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        theme_menu.add_command(
            label="Light",
            command=lambda: self.set_app_theme("light"),
        )
        theme_menu.add_command(
            label="Dark",
            command=lambda: self.set_app_theme("dark"),
        )
        theme_menu.add_separator()
        theme_menu.add_command(
            label="Toggle Dark/Light",
            accelerator="D",
            command=self._toggle_dark_light,
        )
        theme_menu.add_command(
            label="Theme Editor…",
            command=self.open_theme_editor,
        )
        settings_menu.add_cascade(label="Theme", menu=theme_menu)

        menubar.add_cascade(label="Settings", menu=settings_menu)

        self._create_tools_menu(menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Shortcuts", command=show_shortcuts)
        help_menu.add_command(label="About LifeGrid", command=show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def apply_rule_preset(self, birth: str, survival: str) -> None:
        """Apply a preset by switching to Custom Rules and applying B/S."""

        if self.tk_vars.mode.get() != "Custom Rules":
            self.tk_vars.mode.set("Custom Rules")
            self.switch_mode("Custom Rules")

        self.custom_birth_text = birth.strip()
        self.custom_survival_text = survival.strip()
        self.apply_custom_rules(
            birth_text=self.custom_birth_text,
            survival_text=self.custom_survival_text,
        )

    def open_custom_rules_dialog(self) -> None:
        """Open a dialog to edit and apply custom life-like B/S rules."""

        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Rules")
        dialog.transient(self.root)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        ttk.Label(container, text="Birth (B)").grid(
            row=0,
            column=0,
            sticky="w",
        )
        birth_var = tk.StringVar(value=self.custom_birth_text)
        birth_entry = ttk.Entry(container, textvariable=birth_var, width=20)
        birth_entry.grid(row=1, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(container, text="Survival (S)").grid(
            row=2,
            column=0,
            sticky="w",
        )
        survival_var = tk.StringVar(value=self.custom_survival_text)
        survival_entry = ttk.Entry(
            container,
            textvariable=survival_var,
            width=20,
        )
        survival_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))

        hint = (
            "Use digits 0-8. Examples:\n"
            "Conway: B3 / S23\n"
            "HighLife: B36 / S23\n"
            "Seeds: B2 / S∅"
        )
        ttk.Label(container, text=hint, justify=tk.LEFT).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(0, 12),
        )

        buttons = ttk.Frame(container)
        buttons.grid(row=5, column=0, sticky="e")

        def apply_from_dialog() -> None:
            if self.tk_vars.mode.get() != "Custom Rules":
                self.tk_vars.mode.set("Custom Rules")
                self.switch_mode("Custom Rules")
            self.custom_birth_text = birth_var.get().strip()
            self.custom_survival_text = survival_var.get().strip()
            self.apply_custom_rules(
                birth_text=self.custom_birth_text,
                survival_text=self.custom_survival_text,
            )

        apply_btn = ttk.Button(
            buttons,
            text="Apply",
            command=apply_from_dialog,
        )
        apply_btn.grid(row=0, column=0, padx=(0, 8))
        close_btn = ttk.Button(buttons, text="Close", command=dialog.destroy)
        close_btn.grid(row=0, column=1)

        container.columnconfigure(0, weight=1)
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        birth_entry.focus_set()

    def open_simulation_settings(self) -> None:
        """Open a small dialog to adjust simulation parameters."""

        dialog = tk.Toplevel(self.root)
        dialog.title("Grid & View Settings")
        dialog.transient(self.root)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        # Mode/pattern, speed, and drawing controls live in the sidebar.
        grid_size_var = tk.StringVar(value=self.tk_vars.grid_size.get())
        custom_w_var = tk.IntVar(value=self.tk_vars.custom_width.get())
        custom_h_var = tk.IntVar(value=self.tk_vars.custom_height.get())
        cell_size_var = tk.IntVar(value=self.tk_vars.cell_size.get())
        show_grid_var = tk.BooleanVar(value=bool(self.state.show_grid))

        # Grid
        ttk.Label(container, text="Grid Preset").grid(
            row=0,
            column=0,
            sticky="w",
        )
        grid_combo = ttk.Combobox(
            container,
            textvariable=grid_size_var,
            state="readonly",
            values=["50x50", "100x100", "150x150", "200x200", "Custom"],
            width=16,
        )
        grid_combo.grid(row=1, column=0, sticky="w", pady=(2, 6))

        grid_dims = ttk.Frame(container)
        grid_dims.grid(row=2, column=0, sticky="w", pady=(0, 10))
        ttk.Label(grid_dims, text="W").grid(row=0, column=0, sticky="w")
        w_spin = tk.Spinbox(
            grid_dims,
            from_=MIN_GRID_SIZE,
            to=MAX_GRID_SIZE,
            textvariable=custom_w_var,
            width=6,
        )
        w_spin.grid(row=0, column=1, sticky="w", padx=(4, 10))
        ttk.Label(grid_dims, text="H").grid(row=0, column=2, sticky="w")
        h_spin = tk.Spinbox(
            grid_dims,
            from_=MIN_GRID_SIZE,
            to=MAX_GRID_SIZE,
            textvariable=custom_h_var,
            width=6,
        )
        h_spin.grid(row=0, column=3, sticky="w", padx=(4, 0))

        # Cell size
        ttk.Label(container, text="Cell Size").grid(
            row=3,
            column=0,
            sticky="w",
        )
        cell_spin = tk.Spinbox(
            container,
            from_=MIN_CELL_SIZE,
            to=MAX_CELL_SIZE,
            textvariable=cell_size_var,
            width=6,
        )
        cell_spin.grid(row=4, column=0, sticky="w", pady=(2, 10))

        show_grid_check = ttk.Checkbutton(
            container,
            text="Show Grid Lines",
            variable=show_grid_var,
        )
        show_grid_check.grid(row=5, column=0, sticky="w", pady=(0, 12))

        buttons = ttk.Frame(container)
        buttons.grid(row=6, column=0, sticky="e")

        def apply_settings() -> None:
            # Grid preset/custom size
            self.tk_vars.grid_size.set(grid_size_var.get())
            self.tk_vars.custom_width.set(int(custom_w_var.get()))
            self.tk_vars.custom_height.set(int(custom_h_var.get()))
            if grid_size_var.get() == "Custom":
                self.apply_custom_grid_size()
            else:
                self.on_size_preset_change(  # type: ignore[call-arg]
                    tk.Event()
                )

            # Cell size
            self.tk_vars.cell_size.set(int(cell_size_var.get()))
            self.apply_cell_size()

            # View
            self.state.show_grid = bool(show_grid_var.get())
            self._update_display()

        apply_btn = ttk.Button(buttons, text="Apply", command=apply_settings)
        apply_btn.grid(row=0, column=0, padx=(0, 8))
        close_btn = ttk.Button(buttons, text="Close", command=dialog.destroy)
        close_btn.grid(row=0, column=1)

        container.columnconfigure(0, weight=1)
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

    # ------------------------------------------------------------------
    # Variable and widget helpers
    # ------------------------------------------------------------------

    def _save_settings(self) -> None:
        """Apply current state to config and save to file."""
        self.config.automaton_mode = self.tk_vars.mode.get()
        self.config.default_pattern = self.tk_vars.pattern.get()
        self.config.speed = self.tk_vars.speed.get()

        # Grid settings
        self.config.grid_size_selection = self.tk_vars.grid_size.get()
        self.config.custom_width = self.tk_vars.custom_width.get()
        self.config.custom_height = self.tk_vars.custom_height.get()

        # View settings
        self.config.cell_size = self.tk_vars.cell_size.get()
        self.config.draw_mode = self.tk_vars.draw_mode.get()
        self.config.symmetry = self.tk_vars.symmetry.get()
        self.config.show_grid = self.state.show_grid

        # Rules
        self.config.custom_birth = self.custom_birth_text
        self.config.custom_survival = self.custom_survival_text
        self.config.theme = self.theme_manager.get_theme()

        try:
            self.config.save("settings.json")
        except OSError as e:
            print(f"Warning: Failed to save settings: {e}")

    def _load_plugins(self) -> None:
        """Load plugins and register them."""
        # Load from project 'plugins' directory
        plugin_dir = "plugins"
        count = self.plugin_manager.load_plugins_from_directory(plugin_dir)
        if count > 0:
            print(f"Loaded {count} plugins from {plugin_dir}")

        # Register plugins into factory and pattern lists
        for name in self.plugin_manager.list_plugins():
            plugin = self.plugin_manager.get_plugin(name)
            if plugin:
                # Add factory
                MODE_FACTORIES[name] = plugin.create_automaton
                # Add default pattern
                MODE_PATTERNS[name] = ["Random Soup"]

    def _create_variables(self) -> TkVars:
        # Ensure we always start from a valid default on cold start.
        default_mode = "Conway's Game of Life"

        requested_mode = self.config.automaton_mode
        valid_modes = set(MODE_FACTORIES.keys()) | {"Custom Rules"}
        mode = (
            requested_mode if requested_mode in valid_modes else default_mode
        )

        available_patterns = MODE_PATTERNS.get(mode, ["Empty"])
        requested_pattern = self.config.default_pattern
        pattern = (
            requested_pattern
            if requested_pattern in available_patterns
            else available_patterns[0]
        )

        return TkVars(
            mode=tk.StringVar(value=mode),
            pattern=tk.StringVar(value=pattern),
            speed=tk.IntVar(value=self.config.speed),
            grid_size=tk.StringVar(value=self.config.grid_size_selection),
            custom_width=tk.IntVar(value=self.config.custom_width),
            custom_height=tk.IntVar(value=self.config.custom_height),
            cell_size=tk.IntVar(value=self.config.cell_size),
            draw_mode=tk.StringVar(value=self.config.draw_mode),
            symmetry=tk.StringVar(value=self.config.symmetry),
        )

    def _snapshot_grid(self) -> None:
        """Store a copy of the current grid for backward stepping."""

        automaton = self.state.current_automaton
        if automaton and hasattr(automaton, "grid"):
            self.state.grid_history.append(
                np.copy(automaton.grid)  # type: ignore[attr-defined]
            )

    def _reset_history_with_current_grid(self) -> None:
        """Clear history and seed it with the current grid."""

        self.state.grid_history.clear()
        self._snapshot_grid()

    def _update_pattern_description(self) -> None:
        """Show a short description for the selected pattern if available."""

        mode = self.tk_vars.mode.get()
        pattern = self.tk_vars.pattern.get()
        description = get_pattern_description(mode, pattern)
        if not description:
            description = f"{pattern} pattern preset"
        self.widgets.pattern_help.config(text=description)

    def _configure_bindings(self) -> None:
        self.root.bind("<space>", lambda _event: self.toggle_simulation())
        self.root.bind("<Key-s>", lambda _event: self.step_once())
        self.root.bind("<Key-S>", lambda _event: self.step_once())
        self.root.bind("<Key-Left>", lambda _event: self.step_back())
        self.root.bind("<Key-c>", lambda _event: self.clear_grid())
        self.root.bind("<Key-C>", lambda _event: self.clear_grid())
        self.root.bind("<Key-g>", lambda _event: self.toggle_grid())
        self.root.bind("<Key-G>", lambda _event: self.toggle_grid())
        self.root.bind("<Control-z>", self.undo_action)
        self.root.bind("<Control-Z>", self.redo_action)
        self.root.bind("<Control-y>", self.redo_action)
        self.root.bind("<Control-Y>", self.redo_action)
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-C>", self.copy_selection)
        self.root.bind("<Control-x>", self.cut_selection)
        self.root.bind("<Control-X>", self.cut_selection)
        self.root.bind("<Control-v>", self.paste_selection)
        self.root.bind("<Control-V>", self.paste_selection)
        # New bindings
        self.root.bind(
            "<Control-Shift-P>",
            lambda _e: self.command_palette.toggle(),
        )
        self.root.bind(
            "<Control-Shift-p>",
            lambda _e: self.command_palette.toggle(),
        )
        self.root.bind(
            "<Key-d>",
            lambda _e: self._toggle_dark_light(),
        )
        self.root.bind(
            "<Key-b>",
            lambda _e: self.open_breakpoints_dialog(),
        )
        self.root.bind(
            "<Key-r>",
            lambda _e: self.open_rule_explorer(),
        )

    def _update_widgets_enabled_state(self) -> None:
        # Custom-rules controls are now in the Settings menu.
        return

    # ------------------------------------------------------------------
    # Automaton control
    # ------------------------------------------------------------------
    def switch_mode(self, mode_name: str) -> None:
        """Switch to the requested automaton mode and refresh the grid."""

        self.stop_simulation()
        if mode_name == "Custom Rules":
            automaton = LifeLikeAutomaton(
                self.state.grid_width,
                self.state.grid_height,
                self.custom_birth,
                self.custom_survival,
            )
            self.state.current_automaton = automaton
        else:
            factory = MODE_FACTORIES.get(mode_name)
            if factory is None:
                raise ValueError(f"Unsupported mode: {mode_name}")
            self.state.current_automaton = factory(
                self.state.grid_width,
                self.state.grid_height,
            )

        patterns = MODE_PATTERNS.get(mode_name, ["Empty"])
        self.widgets.pattern_combo["values"] = patterns
        self.tk_vars.pattern.set(patterns[0])

        automaton = self.state.current_automaton  # type: ignore[assignment]
        if patterns:
            first_pattern = patterns[0]
        else:
            first_pattern = "Empty"
        if first_pattern != "Empty" and hasattr(automaton, "load_pattern"):
            automaton.load_pattern(first_pattern)  # type: ignore[attr-defined]

        self.state.reset_generation()
        self._reset_history_with_current_grid()
        self._update_generation_label()
        self._update_widgets_enabled_state()
        self._update_display()
        self._update_pattern_description()

    def load_pattern_handler(self) -> None:
        """Load the currently selected pattern into the simulation grid."""

        automaton = self.state.current_automaton
        if not automaton:
            return
        pattern_name = self.tk_vars.pattern.get()
        if pattern_name == "Empty":
            automaton.reset()
        elif hasattr(automaton, "load_pattern"):
            automaton.load_pattern(pattern_name)  # type: ignore[attr-defined]
        self.state.reset_generation()
        self._reset_history_with_current_grid()
        self._update_generation_label()
        self._update_display()
        self._update_pattern_description()

    def toggle_simulation(self) -> None:
        """Start or pause the simulation loop."""

        self.state.running = not self.state.running
        if self.state.running:
            self.widgets.start_button.config(  # type: ignore[attr-defined]
                text="Stop"
            )
            self.root.after(0, self._run_simulation_loop)
        else:
            self.widgets.start_button.config(  # type: ignore[attr-defined]
                text="Start"
            )

    def stop_simulation(self) -> None:
        """Force the simulation into a stopped state."""

        self.state.running = False
        self.widgets.start_button.config(  # type: ignore[attr-defined]
            text="Start"
        )

    def _run_simulation_loop(self) -> None:
        """Advance the automaton while the simulation is marked running."""

        if not self.state.running:
            return
        self.step_once()
        delay = max(10, 1010 - self.tk_vars.speed.get() * 10)
        self.root.after(delay, self._run_simulation_loop)

    def step_once(self) -> None:
        """Advance the automaton by a single generation."""

        automaton = self.state.current_automaton
        if not automaton:
            return
        if not self.state.grid_history:
            self._snapshot_grid()
        automaton.step()
        self.state.generation += 1
        self._snapshot_grid()
        self._update_generation_label()
        self._update_display()

        # Feed timeline + graph + breakpoints
        history_len = len(self.state.grid_history)
        self._timeline.update_range(
            max(0, history_len - 1), self.state.generation,
        )
        grid = automaton.get_grid()
        pop = int(np.count_nonzero(grid))
        ent = 0.0
        cplx = 0
        if self.state.entropy_history:
            ent = self.state.entropy_history[-1]
        if self.state.complexity_history:
            cplx = self.state.complexity_history[-1]
        self._pop_graph.push(pop, ent, cplx)

        self._check_breakpoints()

    def step_back(self) -> None:
        """Revert to the previous generation if history exists."""

        automaton = self.state.current_automaton
        history = self.state.grid_history
        if not (automaton and len(history) > 1 and hasattr(automaton, "grid")):
            return
        # Discard current snapshot and restore the previous one
        history.pop()
        previous_grid = history[-1]
        automaton.grid = np.copy(previous_grid)  # type: ignore[attr-defined]
        self.state.rebuild_stats_from_history()
        self._update_generation_label()
        self._update_display()

    def _push_undo(self, action_name: str = "Edit") -> None:
        """Push the current state to the undo stack."""
        automaton = self.state.current_automaton
        if getattr(automaton, "grid", None) is None or automaton is None:
            return

        # Snapshot current grid and generation
        snapshot = (
            np.copy(automaton.grid),  # type: ignore
            self.state.generation,
        )
        self.state.undo_manager.push_state(action_name, snapshot)

    def undo_action(self, _event: tk.Event | None = None) -> None:
        """Undo the last action."""
        automaton = self.state.current_automaton
        if getattr(automaton, "grid", None) is None or automaton is None:
            return

        current_snapshot = (
            automaton.grid,  # type: ignore
            self.state.generation,
        )

        result = self.state.undo_manager.undo(current_snapshot)
        if result:
            _, (grid, generation) = result
            self._restore_state(grid, generation)
            self._update_display()

    def redo_action(self, _event: tk.Event | None = None) -> None:
        """Redo the last undone action."""
        automaton = self.state.current_automaton
        if getattr(automaton, "grid", None) is None or automaton is None:
            return

        current_snapshot = (
            automaton.grid,  # type: ignore
            self.state.generation,
        )

        result = self.state.undo_manager.redo(current_snapshot)
        if result:
            _, (grid, generation) = result
            self._restore_state(grid, generation)
            self._update_display()

    def _restore_state(self, grid: np.ndarray, generation: int) -> None:
        """Restore internal state from a snapshot."""
        automaton = self.state.current_automaton
        if automaton:
            automaton.grid = np.copy(grid)  # type: ignore

        self.state.generation = generation
        self.state.rebuild_stats_from_history()
        self._update_generation_label()
        self._update_display()

    def copy_selection(self, _event: tk.Event | None = None) -> None:
        """Copy the selected area to the clipboard."""
        rect = self.tool_manager.get_selection_rect()
        automaton = self.state.current_automaton
        if not (rect and automaton):
            return

        x1, y1, x2, y2 = rect
        # Slicing is exclusive at the end, so add 1
        region = automaton.grid[y1 : y2 + 1, x1 : x2 + 1]

        points = []
        rows, cols = region.shape
        for r in range(rows):
            for c in range(cols):
                if region[r, c] == 1:
                    points.append((c, r))

        stamp = Stamp("Clipboard", points)
        self.tool_manager.set_clipboard(stamp)
        # Visual feedback via clearing selection is optional,
        # but let's keep the selection visible to confirm what was copied.

    def cut_selection(self, _event: tk.Event | None = None) -> None:
        """Cut the selected area to the clipboard."""
        rect = self.tool_manager.get_selection_rect()
        automaton = self.state.current_automaton
        if not (rect and automaton):
            return

        self._push_undo("Cut")
        self.copy_selection()

        x1, y1, x2, y2 = rect
        automaton.grid[y1 : y2 + 1, x1 : x2 + 1] = 0

        self.tool_manager.clear_selection()
        self._update_display()

    def paste_selection(self, _event: tk.Event | None = None) -> None:
        """Enter stamp mode with the clipboard content."""
        stamp = self.tool_manager.get_clipboard()
        if stamp:
            self.tool_manager.set_stamp(stamp)
        else:
            messagebox.showwarning("Paste", "Clipboard is empty.")

    def _update_generation_label(self) -> None:
        generation_text = f"Generation: {self.state.generation}"
        self.widgets.gen_label.config(  # type: ignore[attr-defined]
            text=generation_text
        )

    def reset_simulation(self) -> None:
        """Reset the automaton grid to its starting state."""

        automaton = self.state.current_automaton
        if not automaton:
            return
        self.stop_simulation()
        self._push_undo("Reset Simulation")
        automaton.reset()
        self.state.reset_generation()
        self._reset_history_with_current_grid()
        self._update_generation_label()
        self._update_display()
        self._pop_graph.clear_data()
        self._timeline.update_range(0, 0)

    def clear_grid(self) -> None:
        """Clear the grid and pause the simulation."""

        automaton = self.state.current_automaton
        if not automaton:
            return
        self.stop_simulation()
        self._push_undo("Clear Grid")
        automaton.reset()
        self.state.reset_generation()
        self._reset_history_with_current_grid()
        self._update_generation_label()
        self._update_display()
        self._pop_graph.clear_data()
        self._timeline.update_range(0, 0)

    def apply_custom_rules(
        self,
        *,
        birth_text: str | None = None,
        survival_text: str | None = None,
    ) -> None:
        """Apply custom birth/survival rule strings to the automaton."""

        automaton = self.state.current_automaton
        if not isinstance(automaton, LifeLikeAutomaton):
            messagebox.showinfo(
                "Not Custom Mode",
                "Switch to Custom Rules to apply B/S settings.",
            )
            return

        birth_text = (
            birth_text if birth_text is not None else self.custom_birth_text
        ).strip()
        survival_text = (
            survival_text
            if survival_text is not None
            else self.custom_survival_text
        ).strip()

        # Validate input
        if not birth_text and not survival_text:
            messagebox.showerror(
                "Invalid Input",
                "At least one of birth or survival rules must be specified.",
            )
            return

        try:
            birth_set = {int(ch) for ch in birth_text if ch.isdigit()}
            survival_set = {int(ch) for ch in survival_text if ch.isdigit()}

            # Check for valid neighbor counts (0-8)
            invalid_birth = birth_set - set(range(9))
            invalid_survival = survival_set - set(range(9))
            if invalid_birth or invalid_survival:
                invalid = sorted(invalid_birth | invalid_survival)
                messagebox.showerror(
                    "Invalid Input",
                    f"Neighbor counts must be between 0-8. Invalid: {invalid}",
                )
                return

        except ValueError as exc:
            messagebox.showerror(
                "Invalid Input",
                f"Failed to parse rules: {exc}",
            )
            return

        self.custom_birth = birth_set
        self.custom_survival = survival_set
        self.custom_birth_text = birth_text
        self.custom_survival_text = survival_text
        automaton.set_rules(self.custom_birth, self.custom_survival)
        automaton.reset()
        self.state.reset_generation()
        self._reset_history_with_current_grid()
        self._update_generation_label()
        self._update_display()

        # Create user-friendly rule description
        birth_str = (
            "".join(str(n) for n in sorted(birth_set)) if birth_set else "∅"
        )
        survival_str = (
            "".join(str(n) for n in sorted(survival_set))
            if survival_set
            else "∅"
        )
        rule_notation = f"B{birth_str}/S{survival_str}"

        messagebox.showinfo(
            "Rules Applied",
            f"Custom rule: {rule_notation}\n\n"
            f"Birth: {sorted(birth_set) if birth_set else 'Never'}\n"
            f"Survival: {sorted(survival_set) if survival_set else 'Never'}",
        )

    # ------------------------------------------------------------------
    # Grid size helpers
    # ------------------------------------------------------------------
    def on_size_preset_change(self, _event: tk.Event[tk.Misc]) -> None:
        """Resize the grid when a preset dimension is selected."""

        preset = self.tk_vars.grid_size.get()
        if preset == "Custom":
            return
        try:
            width_str, height_str = preset.split("x", 1)
            width = int(width_str)
            height = int(height_str)
        except ValueError:
            messagebox.showerror(
                "Invalid size",
                f"Could not parse preset '{preset}'.",
            )
            return
        self.resize_grid(width, height)

    def apply_custom_grid_size(self) -> None:
        """Resize the grid based on custom width and height spinboxes."""

        self.resize_grid(
            self.tk_vars.custom_width.get(),
            self.tk_vars.custom_height.get(),
        )

    def resize_grid(self, width: int, height: int) -> None:
        """Clamp and apply a new grid size, rebuilding the automaton."""

        width = max(MIN_GRID_SIZE, min(width, MAX_GRID_SIZE))
        height = max(MIN_GRID_SIZE, min(height, MAX_GRID_SIZE))
        self.state.grid_width = width
        self.state.grid_height = height
        self.state.current_automaton = None
        self.switch_mode(self.tk_vars.mode.get())

    def apply_cell_size(self) -> None:
        """Update the rendered cell size and redraw."""

        size = self.tk_vars.cell_size.get()
        size = max(MIN_CELL_SIZE, min(size, MAX_CELL_SIZE))
        self.tk_vars.cell_size.set(size)
        self.state.cell_size = size
        self._update_display()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_pattern(self) -> None:
        """Persist the current grid and rules to a JSON file."""

        automaton = self.state.current_automaton
        if not automaton:
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filename:
            return
        grid = automaton.get_grid()
        payload = {
            "mode": self.tk_vars.mode.get(),
            "width": self.state.grid_width,
            "height": self.state.grid_height,
            "grid": grid.tolist(),
        }
        if isinstance(automaton, LifeLikeAutomaton):
            payload["birth"] = sorted(automaton.birth)
            payload["survival"] = sorted(automaton.survival)
        try:
            with open(filename, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            messagebox.showinfo("Saved", "Pattern saved successfully.")
        except OSError as exc:
            messagebox.showerror(
                "Save Failed",
                f"Could not save pattern: {exc}",
            )

    def load_saved_pattern(self) -> None:
        """Load a pattern JSON file into the active automaton."""

        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(
                "Load Failed",
                f"Could not read file '{filename}': {exc}",
            )
            return

        # Validate required fields
        required_fields = ["mode", "width", "height", "grid"]
        missing_fields = [
            field for field in required_fields if field not in data
        ]
        if missing_fields:
            messagebox.showerror(
                "Invalid File",
                f"Missing required fields: {missing_fields}",
            )
            return

        try:
            mode = data["mode"]
            width = int(data["width"])
            height = int(data["height"])
            grid_data = np.array(data["grid"], dtype=int)
        except (ValueError, KeyError) as exc:
            messagebox.showerror(
                "Invalid Data",
                f"Invalid data format: {exc}",
            )
            return

        # Validate dimensions
        if (
            width < 10
            or width > MAX_GRID_SIZE
            or height < 10
            or height > MAX_GRID_SIZE
        ):
            messagebox.showerror(
                "Invalid Size",
                (
                    "Grid size must be between 10x10 and "
                    f"{MAX_GRID_SIZE}x{MAX_GRID_SIZE}"
                ),
            )
            return

        # Validate grid data
        expected_size = width * height
        if grid_data.size != expected_size:
            messagebox.showerror(
                "Invalid Grid",
                (
                    f"Grid data size ({grid_data.size}) doesn't match "
                    f"dimensions ({width}x{height} = {expected_size})"
                ),
            )
            return

        self.state.grid_width = width
        self.state.grid_height = height
        self.tk_vars.mode.set(mode)
        self.switch_mode(mode)

        automaton = self.state.current_automaton
        if isinstance(automaton, LifeLikeAutomaton):
            birth = data.get("birth", [])
            survival = data.get("survival", [])
            try:
                birth_set = {int(value) for value in birth}
                survival_set = {int(value) for value in survival}
                self.custom_birth = birth_set
                self.custom_survival = survival_set
                self.custom_birth_text = "".join(
                    str(n) for n in sorted(self.custom_birth)
                )
                self.custom_survival_text = "".join(
                    str(n) for n in sorted(self.custom_survival)
                )
                automaton.set_rules(birth_set, survival_set)
            except (ValueError, TypeError):
                messagebox.showwarning(
                    "Invalid Rules",
                    "Could not load custom rules, using defaults.",
                )

        try:
            expected_shape = (self.state.grid_height, self.state.grid_width)
            if automaton is not None and hasattr(automaton, "grid"):
                setattr(
                    automaton,
                    "grid",
                    grid_data.reshape(expected_shape),
                )
        except ValueError:
            messagebox.showwarning(
                "Shape Mismatch",
                (
                    "Saved grid size did not match current settings. "
                    "Resetting grid."
                ),
            )
            if automaton is not None:
                automaton.reset()

        self.state.reset_generation()
        self._update_generation_label()
        self._update_display()
        messagebox.showinfo("Loaded", f"Pattern loaded from {filename}")

    def export_png(self) -> None:
        """Export the current grid as a Pillow PNG image."""

        if not (PIL_AVAILABLE and self.state.current_automaton and PILImage):
            messagebox.showerror(
                "Unavailable",
                "Pillow is required for PNG export.",
            )
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if not filename:
            return
        grid = self.state.current_automaton.get_grid()
        image = PILImage.new(
            "RGB",
            (self.state.grid_width, self.state.grid_height),
            "white",
        )
        pixels = image.load()
        if pixels is None:
            messagebox.showerror(
                "Export Failed",
                "Could not access PNG pixel buffer.",
            )
            return
        for y in range(self.state.grid_height):
            for x in range(self.state.grid_width):
                value = int(grid[y, x])
                pixels[x, y] = EXPORT_COLOR_MAP.get(
                    value,
                    (0, 0, 0),
                )
        max_dimension = max(
            self.state.grid_width,
            self.state.grid_height,
        )
        scale = max(1, 800 // max_dimension)
        image = image.resize(
            (self.state.grid_width * scale, self.state.grid_height * scale),
            _nearest_resample_filter(),  # type: ignore[arg-type]
        )
        try:
            image.save(filename)
            messagebox.showinfo("Exported", f"PNG saved to {filename}")
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Could not save PNG: {exc}")

    # ------------------------------------------------------------------
    # Rendering and interactions
    # ------------------------------------------------------------------
    def _update_display(self) -> None:
        """Redraw the canvas and population statistics."""

        automaton = self.state.current_automaton
        if not (automaton and self.widgets.canvas):
            return
        grid = automaton.get_grid()

        # Build color map for rendering
        theme = self.theme_manager.get_colors()

        # Override 0/1 with theme colors
        colors = CELL_COLORS.copy()
        colors[0] = theme["cell_dead"]
        colors[1] = theme["cell_alive"]

        geometry = (
            "hexagonal"
            if isinstance(automaton, HexagonalGameOfLife)
            else "square"
        )

        draw_grid(
            self.widgets.canvas,
            grid,
            self.state.cell_size,
            self.state.show_grid,
            colors=colors,
            grid_line_color=theme["grid_line"],
            geometry=geometry,
        )

        # Overlay selection box if active
        sel_rect = self.tool_manager.get_selection_rect()
        if sel_rect and geometry == "square":
            x1, y1, x2, y2 = sel_rect
            cs = self.state.cell_size
            self.widgets.canvas.create_rectangle(
                x1 * cs,
                y1 * cs,
                (x2 + 1) * cs,
                (y2 + 1) * cs,
                outline="#facc15",  # Yellow-400
                width=2,
                dash=(4, 2),
                tags="selection_overlay",
            )  # type: ignore[call-overload]

        stats = self.state.update_population_stats(grid)
        self.widgets.population_label.config(  # type: ignore[attr-defined]
            text=stats
        )

    def toggle_grid(self) -> None:
        """Toggle grid line visibility and refresh the canvas."""

        self.state.show_grid = not self.state.show_grid
        self._update_display()

    def _get_grid_coordinates(
        self, event: tk.Event[tk.Misc]
    ) -> tuple[int, int]:
        """Convert canvas coordinates to grid indices."""
        automaton = self.state.current_automaton
        if not (automaton and self.widgets.canvas):
            return -1, -1

        canvas_x = self.widgets.canvas.canvasx(event.x)
        canvas_y = self.widgets.canvas.canvasy(event.y)

        if isinstance(automaton, HexagonalGameOfLife):
            # Approximate hex hit test
            # Geometry matching _draw_hex_grid in rendering.py
            cell_size = self.state.cell_size
            radius = cell_size / 1.73205  # sqrt(3)
            row_height = 1.5 * radius

            y = int(canvas_y / row_height)

            # Odd-r offset logic
            x_shift = (cell_size / 2) if (y % 2) else 0
            x = int((canvas_x - x_shift) / cell_size)
        else:
            x = int(canvas_x // self.state.cell_size)
            y = int(canvas_y // self.state.cell_size)

        return x, y

    def on_canvas_click(self, event: tk.Event[tk.Misc]) -> None:
        """Handle a canvas click based on the active draw mode."""
        x, y = self._get_grid_coordinates(event)
        if not (
            0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height
        ):
            return

        if self.tool_manager.active_tool == "selection":
            self.tool_manager.selection_start = (x, y)
            self.tool_manager.selection_end = (x, y)
            self._update_display()
            return

        self._push_undo("Draw")
        self._apply_draw_action(x, y)
        self._update_display()

    def on_canvas_drag(self, event: tk.Event[tk.Misc]) -> None:
        """Handle a canvas drag while the pointer button is held."""
        x, y = self._get_grid_coordinates(event)
        if not (
            0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height
        ):
            return

        if self.tool_manager.active_tool == "selection":
            if self.tool_manager.selection_start:
                self.tool_manager.selection_end = (x, y)
                self._update_display()
            return

        self._apply_draw_action(x, y)
        self._update_display()

    def _apply_draw_action(self, x: int, y: int) -> None:
        """Apply the selected drawing action at the given grid coordinate."""

        automaton = self.state.current_automaton
        if not automaton:
            return

        # Stamp Logic
        if self.tool_manager.is_stamp_active():
            stamp = self.tool_manager.get_stamp()
            if stamp and stamp.points:
                for dx, dy in stamp.points:
                    target_x = x + dx
                    target_y = y + dy
                    if (
                        0 <= target_x < self.state.grid_width
                        and 0 <= target_y < self.state.grid_height
                    ):
                        automaton.grid[target_y, target_x] = 1
            return

        positions = symmetry_positions(
            x,
            y,
            self.state.grid_width,
            self.state.grid_height,
            self.tk_vars.symmetry.get(),
        )

        for px, py in positions:
            within_width = 0 <= px < self.state.grid_width
            within_height = 0 <= py < self.state.grid_height
            if not (within_width and within_height):
                continue

            # Tools override 'Toggle' vs 'Pen' behavior from draw_mode
            if self.tool_manager.active_tool == "eraser":
                automaton.grid[py, px] = 0
            elif self.tool_manager.active_tool == "pencil":
                # Use existing Draw Mode logic for pencil
                if self.tk_vars.draw_mode.get() == "toggle":
                    automaton.handle_click(px, py)
                elif self.tk_vars.draw_mode.get() == "pen":
                    automaton.grid[py, px] = 1
                elif self.tk_vars.draw_mode.get() == "eraser":
                    # Fallback if UI still has Eraser in legacy dropdown
                    automaton.grid[py, px] = 0

    def export_metrics(self) -> None:
        """Export per-generation metrics to CSV."""

        if not self.state.metrics_log:
            messagebox.showinfo(
                "No Data",
                "Run the simulation to collect metrics before exporting.",
            )
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return

        fieldnames = [
            "generation",
            "live",
            "delta",
            "density",
            "entropy",
            "complexity",
            "cycle_period",
        ]
        try:
            with open(filename, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.state.metrics_log:
                    writer.writerow(row)
            messagebox.showinfo("Exported", f"Metrics saved to {filename}")
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Could not save CSV: {exc}")

    # ------------------------------------------------------------------
    # New features
    # ------------------------------------------------------------------

    def _seek_generation(self, idx: int) -> None:
        """Jump to a specific generation in the grid history."""
        history = list(self.state.grid_history)
        if not history:
            return
        idx = max(0, min(idx, len(history) - 1))
        automaton = self.state.current_automaton
        if automaton and hasattr(automaton, "grid"):
            automaton.grid = np.copy(history[idx])
            self.state.generation = idx
            self._update_generation_label()
            self._update_display()

    def _register_palette_commands(self) -> None:
        """Register all commands in the command palette."""
        p = self.command_palette
        p.register("Start / Stop Simulation", self.toggle_simulation)
        p.register("Step Forward", self.step_once)
        p.register("Step Backward", self.step_back)
        p.register("Clear Grid", self.clear_grid)
        p.register("Reset Simulation", self.reset_simulation)
        p.register("Toggle Grid Lines", self.toggle_grid)
        p.register("Save Pattern...", self.save_pattern)
        p.register("Load Pattern...", self.load_saved_pattern)
        p.register("Import RLE...", self.load_rle_pattern)
        p.register("Export Metrics (CSV)...", self.export_metrics)
        if PIL_AVAILABLE:
            p.register("Export PNG...", self.export_png)
        p.register("Undo", self.undo_action)
        p.register("Redo", self.redo_action)
        p.register("Open Rule Explorer", self.open_rule_explorer)
        p.register("Open Breakpoints", self.open_breakpoints_dialog)
        p.register("Open Theme Editor", self.open_theme_editor)
        p.register(
            "Open Pattern Shape Search",
            self.open_pattern_shape_search,
        )
        p.register("Switch to Dark Theme", lambda: self.set_app_theme("dark"))
        p.register(
            "Switch to Light Theme", lambda: self.set_app_theme("light"),
        )
        p.register("Boundary: Wrap", lambda: self._set_boundary("wrap"))
        p.register("Boundary: Fixed", lambda: self._set_boundary("fixed"))
        p.register("Boundary: Reflect", lambda: self._set_boundary("reflect"))
        p.register(
            "Toggle Dark/Light",
            self._toggle_dark_light,
        )

    def _set_boundary(self, mode_name: str) -> None:
        """Change the boundary mode."""
        self.boundary_mode = BoundaryMode.from_string(mode_name)

    def _toggle_dark_light(self) -> None:
        """Quick toggle between dark and light themes."""
        current = self.theme_manager.get_theme()
        new = "dark" if current == "light" else "light"
        self.set_app_theme(new)

    def open_rule_explorer(self) -> None:
        """Open the interactive Rule Explorer dialog."""
        def apply_rule(b_text: str, s_text: str) -> None:
            self.apply_rule_preset(b_text, s_text)

        RuleExplorer(self.root, on_apply=apply_rule)

    def open_breakpoints_dialog(self) -> None:
        """Open the simulation breakpoints manager."""
        BreakpointDialog(self.root, self.breakpoint_manager)

    def open_theme_editor(self) -> None:
        """Open the custom theme editor."""
        current = self.theme_manager.get_colors()

        def apply_custom(colors: dict[str, str]) -> None:
            self.theme_manager.set_custom_colors(colors)
            self._apply_theme_colors()
            self._update_display()

        ThemeEditorDialog(self.root, current, on_apply=apply_custom)

    def open_pattern_shape_search(self) -> None:
        """Open the visual pattern search dialog."""
        # Build pattern dict from PATTERN_DATA
        all_patterns: dict[str, list[tuple[int, int]]] = {}
        for mode_pats in PATTERN_DATA.values():
            if isinstance(mode_pats, dict):
                for name, (points, _desc) in mode_pats.items():
                    all_patterns[name] = points

        def on_select(name: str) -> None:
            automaton = self.state.current_automaton
            if not automaton:
                return
            # Find the points
            pts = all_patterns.get(name)
            if pts and hasattr(automaton, "grid"):
                automaton.grid[:] = 0
                cx = self.state.grid_width // 2
                cy = self.state.grid_height // 2
                for dx, dy in pts:
                    x, y = cx + dx, cy + dy
                    if (
                        0 <= x < self.state.grid_width
                        and 0 <= y < self.state.grid_height
                    ):
                        automaton.grid[y, x] = 1
                self.state.reset_generation()
                self._reset_history_with_current_grid()
                self._update_generation_label()
                self._update_display()

        PatternShapeSearch(self.root, on_select, all_patterns)

    def _check_breakpoints(self) -> None:
        """Check if any breakpoint conditions are met."""
        if not self.state.metrics_log:
            return
        last = self.state.metrics_log[-1]
        # Map metric keys to breakpoint keys
        metrics_for_bp = {
            "population": last.get("live", 0),
            "entropy": last.get("entropy", 0.0),
            "complexity": last.get("complexity", 0),
            "generation": self.state.generation,
        }
        triggered = self.breakpoint_manager.check_all(metrics_for_bp)
        if triggered:
            self.stop_simulation()
            messagebox.showinfo(
                "Breakpoint Hit",
                f"Breakpoint triggered: {triggered}",
            )


def launch() -> None:
    """Create the Tk root window and start the simulator event loop."""

    root = tk.Tk()
    AutomatonApp(root)
    root.mainloop()
