"""Generation timeline scrubber, breakpoint system, and population graph.

These are self-contained widgets that plug into AutomatonApp via simple
``attach(app)`` calls.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from typing import (
    TYPE_CHECKING,
    Callable,
    Deque,
    Optional,
)

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    pass


# ======================================================================
#  1. Generation Timeline / Scrubber
# ======================================================================

class GenerationTimeline(ttk.Frame):
    """A slider + playback bar that lets users scrub through history."""

    def __init__(
        self,
        parent: tk.Misc,
        on_seek: Callable[[int], None],
        **kw,
    ) -> None:
        super().__init__(parent, **kw)
        self._on_seek = on_seek
        self._max_gen = 0
        self._current = 0

        # Controls row
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X)

        self._lbl = ttk.Label(ctrl, text="Gen 0 / 0", width=18)
        self._lbl.pack(side=tk.LEFT, padx=(0, 4))

        self._slider = tk.Scale(
            ctrl,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            showvalue=False,
            command=self._on_slider,
            bg="#ffffff",
            highlightthickness=0,
            troughcolor="#e2e8f0",
        )
        self._slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Quick buttons
        ttk.Button(
            ctrl, text="\u23ee", width=3, command=self._go_start,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            ctrl, text="\u23ed", width=3, command=self._go_end,
        ).pack(side=tk.LEFT, padx=2)

    # ------------------------------------------------------------------
    def update_range(self, max_gen: int, current: int) -> None:
        """Call after every step to keep the slider in sync."""
        self._max_gen = max_gen
        self._current = current
        self._slider.configure(to=max(0, max_gen))
        self._slider.set(current)
        self._lbl.configure(text=f"Gen {current} / {max_gen}")

    def _on_slider(self, val: str) -> None:
        idx = int(float(val))
        if idx != self._current:
            self._current = idx
            self._lbl.configure(
                text=f"Gen {idx} / {self._max_gen}"
            )
            self._on_seek(idx)

    def _go_start(self) -> None:
        self._slider.set(0)
        self._on_seek(0)

    def _go_end(self) -> None:
        self._slider.set(self._max_gen)
        self._on_seek(self._max_gen)


# ======================================================================
#  2. Population / Stat Graph
# ======================================================================

class PopulationGraph(tk.Canvas):
    """Live mini-chart of population, entropy, and complexity."""

    COLORS = {
        "population": "#0ea5e9",
        "entropy": "#f59e0b",
        "complexity": "#10b981",
    }

    def __init__(
        self,
        parent: tk.Misc,
        width: int = 280,
        height: int = 100,
        **kw,
    ) -> None:
        super().__init__(
            parent, width=width, height=height,
            bg="#f8fafc", highlightthickness=0, **kw,
        )
        self._graph_w = width
        self._graph_h = height
        self._pop: Deque[int] = deque(maxlen=200)
        self._ent: Deque[float] = deque(maxlen=200)
        self._cplx: Deque[int] = deque(maxlen=200)

    def push(
        self,
        population: int,
        entropy: float = 0.0,
        complexity: int = 0,
    ) -> None:
        """Append one data point and redraw."""
        self._pop.append(population)
        self._ent.append(entropy)
        self._cplx.append(complexity)
        self._redraw()

    def clear_data(self) -> None:
        """Reset the graph data."""
        self._pop.clear()
        self._ent.clear()
        self._cplx.clear()
        self.delete("all")

    # ------------------------------------------------------------------
    def _redraw(self) -> None:
        self.delete("all")
        w, h = self._graph_w, self._graph_h
        pad = 4

        # Draw each series
        self._draw_series(
            list(self._pop), self.COLORS["population"], w, h, pad,
        )
        self._draw_series(
            [e * 100 for e in self._ent],
            self.COLORS["entropy"], w, h, pad, dash=(2, 2),
        )
        self._draw_series(
            list(self._cplx), self.COLORS["complexity"], w, h, pad,
            dash=(4, 2),
        )

        # Legend
        x = 6
        for label, color in self.COLORS.items():
            self.create_rectangle(x, 4, x + 8, 12, fill=color, outline="")
            self.create_text(
                x + 11, 8, text=label[:3].title(),
                anchor=tk.W, font=("Segoe UI", 7), fill="#475569",
            )
            x += 46

    def _draw_series(
        self,
        data: list[float | int],
        color: str,
        w: int,
        h: int,
        pad: int,
        dash: tuple[int, ...] | None = None,
    ) -> None:
        n = len(data)
        if n < 2:
            return
        mn = min(data)
        mx = max(data)
        rng = mx - mn if mx != mn else 1.0

        step = (w - 2 * pad) / (n - 1)
        points: list[float] = []
        for i, v in enumerate(data):
            x = pad + i * step
            y = h - pad - ((v - mn) / rng) * (h - 2 * pad - 16)
            points.extend([x, y])

        kwargs: dict = {"fill": color, "width": 1.5, "smooth": True}
        if dash:
            kwargs["dash"] = dash
        self.create_line(*points, **kwargs)


# ======================================================================
#  3. Breakpoint System
# ======================================================================

class BreakpointCondition:
    """A single breakpoint condition."""

    def __init__(
        self,
        kind: str,
        value: int | float,
        comparator: str = ">=",
        enabled: bool = True,
    ) -> None:
        self.kind = kind          # population, entropy, complexity, generation
        self.value = value
        self.comparator = comparator  # >=, <=, ==
        self.enabled = enabled

    def check(self, metrics: dict) -> bool:
        """Return True if this breakpoint should fire."""
        if not self.enabled:
            return False
        actual = metrics.get(self.kind, 0)
        if self.comparator == ">=":
            return actual >= self.value  # type: ignore[no-any-return]
        if self.comparator == "<=":
            return actual <= self.value  # type: ignore[no-any-return]
        if self.comparator == "==":
            return actual == self.value  # type: ignore[no-any-return]
        return False

    def __str__(self) -> str:
        return f"{self.kind} {self.comparator} {self.value}"


class BreakpointManager:
    """Manages a list of breakpoint conditions."""

    def __init__(self) -> None:
        self.breakpoints: list[BreakpointCondition] = []

    def add(self, bp: BreakpointCondition) -> None:
        self.breakpoints.append(bp)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.breakpoints):
            del self.breakpoints[index]

    def clear(self) -> None:
        self.breakpoints.clear()

    def check_all(self, metrics: dict) -> Optional[BreakpointCondition]:
        """Return the first triggered breakpoint, or None."""
        for bp in self.breakpoints:
            if bp.check(metrics):
                return bp
        return None


class BreakpointDialog:
    """Dialog for managing simulation breakpoints."""

    def __init__(
        self,
        parent: tk.Misc,
        manager: BreakpointManager,
    ) -> None:
        self.manager = manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Breakpoints")
        if isinstance(parent, tk.Wm):
            self.dialog.transient(parent)
        self.dialog.grab_set()

        container = ttk.Frame(self.dialog, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        # List
        self._listbox = tk.Listbox(container, height=8, width=40)
        self._listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self._refresh_list()

        # Add row
        add_frame = ttk.Frame(container)
        add_frame.pack(fill=tk.X, pady=(0, 4))

        self._kind_var = tk.StringVar(value="population")
        ttk.Combobox(
            add_frame,
            textvariable=self._kind_var,
            values=["population", "entropy", "complexity", "generation"],
            state="readonly", width=12,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self._comp_var = tk.StringVar(value=">=")
        ttk.Combobox(
            add_frame,
            textvariable=self._comp_var,
            values=[">=", "<=", "=="],
            state="readonly", width=4,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self._val_var = tk.StringVar(value="100")
        ttk.Entry(
            add_frame, textvariable=self._val_var, width=8,
        ).pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(
            add_frame, text="Add", command=self._add,
        ).pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X)
        ttk.Button(
            btn_frame, text="Remove Selected", command=self._remove,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            btn_frame, text="Clear All", command=self._clear,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            btn_frame, text="Close", command=self.dialog.destroy,
        ).pack(side=tk.RIGHT)

        self.dialog.bind("<Escape>", lambda _e: self.dialog.destroy())

    def _refresh_list(self) -> None:
        self._listbox.delete(0, tk.END)
        for bp in self.manager.breakpoints:
            self._listbox.insert(tk.END, str(bp))

    def _add(self) -> None:
        try:
            val: int | float
            raw = self._val_var.get()
            val = float(raw) if "." in raw else int(raw)
        except ValueError:
            messagebox.showerror("Invalid", "Enter a numeric value.")
            return
        bp = BreakpointCondition(
            self._kind_var.get(), val, self._comp_var.get(),
        )
        self.manager.add(bp)
        self._refresh_list()

    def _remove(self) -> None:
        sel = self._listbox.curselection()
        if sel:
            self.manager.remove(sel[0])
            self._refresh_list()

    def _clear(self) -> None:
        self.manager.clear()
        self._refresh_list()


# ======================================================================
#  4. Rule Explorer / Parameter Playground
# ======================================================================

# Well-known life-like rules for the explorer sidebar
NAMED_RULES: list[tuple[str, str]] = [
    ("Conway (B3/S23)", "B3/S23"),
    ("HighLife (B36/S23)", "B36/S23"),
    ("Seeds (B2/S)", "B2/S"),
    ("Day & Night (B3678/S34678)", "B3678/S34678"),
    ("Morley (B368/S245)", "B368/S245"),
    ("Life w/o Death (B3/S012345678)", "B3/S012345678"),
    ("Diamoeba (B35678/S5678)", "B35678/S5678"),
    ("2x2 (B36/S125)", "B36/S125"),
    ("Anneal (B4678/S35678)", "B4678/S35678"),
    ("Replicator (B1357/S1357)", "B1357/S1357"),
]


class RuleExplorer:
    """Interactive B/S rule panel with checkboxes and presets."""

    def __init__(
        self,
        parent: tk.Misc,
        on_apply: Callable[[str, str], None],
    ) -> None:
        """
        Args:
            on_apply: callback(birth_text, survival_text) invoked on Apply.
        """
        self._on_apply = on_apply
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Rule Explorer")
        if isinstance(parent, tk.Wm):
            self.dialog.transient(parent)
        self.dialog.geometry("380x420")

        container = ttk.Frame(self.dialog, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container, text="Rule Explorer",
            font=("Segoe UI Semibold", 12),
        ).pack(anchor=tk.W, pady=(0, 8))

        # Birth checkboxes
        b_frame = ttk.Labelframe(container, text="Birth (B)")
        b_frame.pack(fill=tk.X, pady=(0, 4))
        self._b_vars: list[tk.BooleanVar] = []
        row = ttk.Frame(b_frame)
        row.pack(fill=tk.X)
        for i in range(9):
            var = tk.BooleanVar(value=(i == 3))
            cb = ttk.Checkbutton(row, text=str(i), variable=var)
            cb.pack(side=tk.LEFT, padx=2)
            self._b_vars.append(var)

        # Survival checkboxes
        s_frame = ttk.Labelframe(container, text="Survival (S)")
        s_frame.pack(fill=tk.X, pady=(0, 4))
        self._s_vars: list[tk.BooleanVar] = []
        row2 = ttk.Frame(s_frame)
        row2.pack(fill=tk.X)
        for i in range(9):
            var = tk.BooleanVar(value=(i in (2, 3)))
            cb = ttk.Checkbutton(row2, text=str(i), variable=var)
            cb.pack(side=tk.LEFT, padx=2)
            self._s_vars.append(var)

        # Rule notation display
        self._rule_var = tk.StringVar(value="B3/S23")
        ttk.Label(
            container, textvariable=self._rule_var,
            font=("Consolas", 11, "bold"),
        ).pack(anchor=tk.W, pady=6)

        # Presets list
        ttk.Label(
            container, text="Presets:", style="Muted.TLabel",
        ).pack(anchor=tk.W)
        preset_frame = ttk.Frame(container)
        preset_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
        self._preset_list = tk.Listbox(preset_frame, height=6)
        self._preset_list.pack(fill=tk.BOTH, expand=True)
        for label, _ in NAMED_RULES:
            self._preset_list.insert(tk.END, label)
        self._preset_list.bind(
            "<<ListboxSelect>>", self._on_preset_select,
        )

        # Buttons
        btn = ttk.Frame(container)
        btn.pack(fill=tk.X)
        ttk.Button(
            btn, text="Apply", style="Primary.TButton",
            command=self._apply,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn, text="Close", command=self.dialog.destroy,
        ).pack(side=tk.LEFT)

        # Wire checkbox changes to rule label
        for v in self._b_vars + self._s_vars:
            v.trace_add("write", self._update_label)

        self.dialog.bind("<Escape>", lambda _e: self.dialog.destroy())

    def _update_label(self, *_args) -> None:  # type: ignore[no-untyped-def]
        b = "".join(str(i) for i, v in enumerate(self._b_vars) if v.get())
        s = "".join(str(i) for i, v in enumerate(self._s_vars) if v.get())
        self._rule_var.set(f"B{b}/S{s}")

    def _on_preset_select(
        self, _event: tk.Event,  # type: ignore[type-arg]
    ) -> None:
        sel = self._preset_list.curselection()
        if not sel:
            return
        _, rule_str = NAMED_RULES[sel[0]]
        # Parse and set checkboxes
        from automata import parse_bs
        birth, survival = parse_bs(rule_str)
        for i, v in enumerate(self._b_vars):
            v.set(i in birth)
        for i, v in enumerate(self._s_vars):
            v.set(i in survival)

    def _apply(self) -> None:
        b = "".join(str(i) for i, v in enumerate(self._b_vars) if v.get())
        s = "".join(str(i) for i, v in enumerate(self._s_vars) if v.get())
        self._on_apply(b, s)


# ======================================================================
#  5. Command Palette
# ======================================================================

class CommandPalette:
    """Ctrl+Shift+P command palette overlay."""

    def __init__(self, parent: tk.Tk) -> None:
        self._parent = parent
        self._commands: list[tuple[str, Callable[[], None]]] = []
        self._visible = False
        self._top: Optional[tk.Toplevel] = None
        self._search_var: tk.StringVar | None = None
        self._listbox: tk.Listbox | None = None
        self._filtered: list[int] = []

    def register(self, label: str, callback: Callable[[], None]) -> None:
        """Register a command."""
        self._commands.append((label, callback))

    def toggle(
        self, _event: tk.Event | None = None,  # type: ignore[type-arg]
    ) -> None:
        """Show or hide the palette."""
        if self._visible:
            self._hide()
        else:
            self._show()

    def _show(self) -> None:
        self._visible = True
        self._top = tk.Toplevel(self._parent)
        self._top.overrideredirect(True)

        # Center above parent
        pw = self._parent.winfo_width()
        px = self._parent.winfo_rootx()
        py = self._parent.winfo_rooty()
        w = min(460, pw - 40)
        self._top.geometry(f"{w}x320+{px + (pw - w) // 2}+{py + 60}")

        frame = ttk.Frame(self._top, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter)
        entry = ttk.Entry(
            frame, textvariable=self._search_var,
            font=("Segoe UI", 11),
        )
        entry.pack(fill=tk.X, pady=(0, 6))
        entry.focus_set()

        self._listbox = tk.Listbox(
            frame, font=("Segoe UI", 10), activestyle="dotbox",
        )
        self._listbox.pack(fill=tk.BOTH, expand=True)
        self._filtered = []
        self._filter()

        self._listbox.bind("<Double-1>", self._execute)
        entry.bind("<Return>", self._execute)
        entry.bind("<Escape>", lambda _e: self._hide())
        self._top.bind("<FocusOut>", lambda _e: self._hide())

    def _hide(self) -> None:
        self._visible = False
        if self._top:
            self._top.destroy()
            self._top = None

    def _filter(self, *_args: object) -> None:
        q = (
            self._search_var.get().lower()
            if self._search_var is not None else ""
        )
        if self._listbox is None:
            return
        self._listbox.delete(0, tk.END)
        self._filtered = []
        for i, (label, _cb) in enumerate(self._commands):
            if q in label.lower():
                self._listbox.insert(tk.END, label)
                self._filtered.append(i)

    def _execute(
        self, _event: tk.Event | None = None,  # type: ignore[type-arg]
    ) -> None:
        if self._listbox is None:
            return
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = self._filtered[sel[0]]
        _, cb = self._commands[idx]
        self._hide()
        cb()


# ======================================================================
#  6. Theme Editor
# ======================================================================

class ThemeEditorDialog:
    """Let users create, preview, and save custom color themes."""

    def __init__(
        self,
        parent: tk.Misc,
        current_colors: dict[str, str],
        on_apply: Callable[[dict[str, str]], None],
    ) -> None:
        self._on_apply = on_apply
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Theme Editor")
        if isinstance(parent, tk.Wm):
            self.dialog.transient(parent)
        self.dialog.geometry("340x420")

        container = ttk.Frame(self.dialog, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container, text="Theme Editor",
            font=("Segoe UI Semibold", 12),
        ).pack(anchor=tk.W, pady=(0, 8))

        self._entries: dict[str, tk.StringVar] = {}
        editable_keys = [
            "bg", "fg", "button_bg", "button_fg",
            "cell_alive", "cell_dead", "grid_line",
        ]

        for key in editable_keys:
            row = ttk.Frame(container)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=key, width=12).pack(side=tk.LEFT)
            var = tk.StringVar(value=current_colors.get(key, "#000000"))
            ent = ttk.Entry(row, textvariable=var, width=10)
            ent.pack(side=tk.LEFT, padx=4)
            # Color preview swatch
            swatch = tk.Canvas(row, width=20, height=20, highlightthickness=0)
            swatch.pack(side=tk.LEFT)
            try:
                swatch.configure(bg=var.get())
            except tk.TclError:
                swatch.configure(bg="#000000")
            self._entries[key] = var

            # Bind live preview of swatch
            def _update_swatch(
                _a, _b, _c, s=swatch, v=var,
            ) -> None:  # type: ignore[no-untyped-def]
                try:
                    s.configure(bg=v.get())
                except tk.TclError:
                    pass
            var.trace_add("write", _update_swatch)

        # Preset buttons
        presets_frame = ttk.Frame(container)
        presets_frame.pack(fill=tk.X, pady=(12, 4))
        ttk.Button(
            presets_frame, text="Dark Preset",
            command=self._set_dark,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            presets_frame, text="Light Preset",
            command=self._set_light,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            presets_frame, text="Ocean Preset",
            command=self._set_ocean,
        ).pack(side=tk.LEFT)

        # Apply / close
        btn = ttk.Frame(container)
        btn.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            btn, text="Apply", style="Primary.TButton",
            command=self._apply,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn, text="Close", command=self.dialog.destroy,
        ).pack(side=tk.LEFT)

        self.dialog.bind("<Escape>", lambda _e: self.dialog.destroy())

    def _set_colors(self, colors: dict[str, str]) -> None:
        for k, v in colors.items():
            if k in self._entries:
                self._entries[k].set(v)

    def _set_dark(self) -> None:
        self._set_colors({
            "bg": "#1e293b", "fg": "#e2e8f0",
            "button_bg": "#334155", "button_fg": "#f1f5f9",
            "cell_alive": "#38bdf8", "cell_dead": "#0f172a",
            "grid_line": "#334155",
        })

    def _set_light(self) -> None:
        self._set_colors({
            "bg": "#ffffff", "fg": "#0f172a",
            "button_bg": "#e2e8f0", "button_fg": "#1e293b",
            "cell_alive": "#000000", "cell_dead": "#ffffff",
            "grid_line": "#cbd5e1",
        })

    def _set_ocean(self) -> None:
        self._set_colors({
            "bg": "#0c4a6e", "fg": "#e0f2fe",
            "button_bg": "#0369a1", "button_fg": "#f0f9ff",
            "cell_alive": "#22d3ee", "cell_dead": "#082f49",
            "grid_line": "#164e63",
        })

    def _apply(self) -> None:
        colors = {k: v.get() for k, v in self._entries.items()}
        self._on_apply(colors)


# ======================================================================
#  7. Pattern Shape Search
# ======================================================================

class PatternShapeSearch:
    """Let users draw a rough shape and search matching patterns."""

    def __init__(
        self,
        parent: tk.Misc,
        on_select: Callable[[str], None],
        available_patterns: dict[str, list[tuple[int, int]]],
    ) -> None:
        self._on_select = on_select
        self._patterns = available_patterns
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Pattern Search by Shape")
        if isinstance(parent, tk.Wm):
            self.dialog.transient(parent)
        self.dialog.geometry("400x460")

        container = ttk.Frame(self.dialog, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container, text="Draw a shape, then Search",
            font=("Segoe UI Semibold", 11),
        ).pack(anchor=tk.W, pady=(0, 6))

        # Drawing canvas (16x16 grid)
        self._grid_size = 16
        cell = 20
        self._cell = cell
        self._canvas = tk.Canvas(
            container,
            width=self._grid_size * cell,
            height=self._grid_size * cell,
            bg="white", highlightthickness=1,
            highlightbackground="#94a3b8",
        )
        self._canvas.pack(pady=(0, 8))
        self._grid = np.zeros(
            (self._grid_size, self._grid_size), dtype=int,
        )
        self._canvas.bind("<B1-Motion>", self._paint)
        self._canvas.bind("<Button-1>", self._paint)
        self._draw_grid()

        btn_row = ttk.Frame(container)
        btn_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(
            btn_row, text="Search", style="Primary.TButton",
            command=self._search,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            btn_row, text="Clear", command=self._clear,
        ).pack(side=tk.LEFT)

        # Results
        self._results_list = tk.Listbox(container, height=6)
        self._results_list.pack(fill=tk.BOTH, expand=True)
        self._results_list.bind(
            "<Double-1>", self._select_result,
        )

        self.dialog.bind("<Escape>", lambda _e: self.dialog.destroy())

    def _draw_grid(self) -> None:
        self._canvas.delete("all")
        cs = self._cell
        for y in range(self._grid_size):
            for x in range(self._grid_size):
                color = "#1e293b" if self._grid[y, x] else "white"
                self._canvas.create_rectangle(
                    x * cs, y * cs, (x + 1) * cs, (y + 1) * cs,
                    fill=color, outline="#e2e8f0",
                )

    def _paint(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        x = int(event.x // self._cell)
        y = int(event.y // self._cell)
        if 0 <= x < self._grid_size and 0 <= y < self._grid_size:
            self._grid[y, x] = 1
            self._draw_grid()

    def _clear(self) -> None:
        self._grid[:] = 0
        self._draw_grid()
        self._results_list.delete(0, tk.END)

    def _search(self) -> None:
        # Extract drawn points (normalized to origin)
        pts = set()
        for y in range(self._grid_size):
            for x in range(self._grid_size):
                if self._grid[y, x]:
                    pts.add((x, y))
        if not pts:
            return

        # Normalize
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        drawn = {(x - min_x, y - min_y) for x, y in pts}

        # Score each pattern by Jaccard similarity
        scores: list[tuple[str, float]] = []
        for name, points in self._patterns.items():
            if not points:
                continue
            pmin_x = min(p[0] for p in points)
            pmin_y = min(p[1] for p in points)
            norm = {(x - pmin_x, y - pmin_y) for x, y in points}
            inter = len(drawn & norm)
            union = len(drawn | norm)
            if union > 0:
                scores.append((name, inter / union))

        scores.sort(key=lambda t: t[1], reverse=True)

        self._results_list.delete(0, tk.END)
        for name, score in scores[:10]:
            self._results_list.insert(
                tk.END, f"{name}  ({score:.0%})",
            )

    def _select_result(
        self, _event: tk.Event,  # type: ignore[type-arg]
    ) -> None:
        sel = self._results_list.curselection()
        if sel:
            text = self._results_list.get(sel[0])
            name = text.rsplit("  (", 1)[0]
            self._on_select(name)
            self.dialog.destroy()
