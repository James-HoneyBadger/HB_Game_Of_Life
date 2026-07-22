# User Guide

This guide covers everyday use of LifeGrid's GUI, drawing tools, simulation controls, and export features.

---

## Launching the GUI

```bash
python src/main.py
# or
make run
```

The main window opens with a grid canvas, toolbar, sidebar, and status bar.

---

## Simulation Controls

| Control | Location | Description |
|---------|----------|-------------|
| **Start / Stop** | Toolbar or `Space` | Toggle continuous simulation |
| **Step** | Toolbar or `S` | Advance one generation |
| **Reset** | Toolbar or `R` | Restore the grid to its initial state |
| **Clear** | Menu or `C` | Set all cells to dead |
| **Speed** | Sidebar slider | Adjust simulation speed (1–100) |

### Undo / Redo

Every step is recorded. Use `Ctrl+Z` to undo and `Ctrl+Y` to redo (up to 100 states).

### Generation Timeline

The timeline slider in the sidebar lets you scrub through previously computed generations. Dragging the slider instantly displays that generation's grid state.

---

## Drawing Tools

Select a tool from the toolbar:

| Tool | Description |
|------|-------------|
| **Pencil** | Click or drag to place live cells |
| **Eraser** | Click or drag to remove cells |
| **Stamp** | Click to place a predefined pattern |
| **Selection** | Click and drag to select a rectangular region |

### Brush Settings

- **Size** — 1 to 10 cells
- **Shape** — square, circle, or diamond

### Stamps

Stamps are small reusable patterns (glider, blinker, etc.). Select a stamp from the stamp palette, then click the canvas to place it.

---

## Modes

Change the automaton mode from the **Mode** menu or sidebar dropdown. Available modes:

- **Conway's Game of Life** (B3/S23)
- **HighLife** (B36/S23)
- **Immigration** — two-color Conway variant
- **Rainbow** — multi-color Conway variant
- **Langton's Ant** — a Turing-complete ant
- **Wireworld** — electronic circuit simulation
- **Brian's Brain** — firing / refractory / ready
- **Generations** — multi-state fading
- **Hexagonal Life** — hexagonal grid
- **Custom Rules** — enter any B/S rule string (e.g., `B36/S23`)

Each mode has its own built-in pattern library.

---

## Patterns

### Loading Patterns

Open the **Pattern Browser** from the menu to browse built-in patterns for the current mode. Select a pattern and click the canvas to place it.

### Importing RLE

Use **File → Import RLE** to load a `.rle` file. The pattern is centered on the grid.

### Exporting RLE

Use **File → Export RLE** to save the current grid in Run-Length Encoded format.

---

## Themes

LifeGrid ships with **light** and **dark** themes. Toggle between them from the **View** menu.

### Theme Editor

Open the theme editor (`View → Theme Editor`) to customize colors:

- Background, grid lines, live/dead cells, UI accent
- Three built-in presets: Default, Ocean, Sunset
- Changes apply in real time

---

## Breakpoints

Breakpoints pause the simulation when a condition is met.

1. Press `B` or use the menu to open the **Breakpoint Manager**.
2. Add a condition:
   - **Population** — equal to, greater than, or less than a value
   - **Generation** — reaches a specific number
   - **Density** — above or below a threshold
3. The simulation pauses automatically when the condition triggers.

---

## Rule Explorer

Press `Ctrl+Shift+R` or use the menu to open the **Rule Explorer**. It lists 10 named Life-like rulesets:

| Name | Rule |
|------|------|
| Seeds | B2/S |
| Day & Night | B3678/S34678 |
| Diamoeba | B35678/S5678 |
| Morley | B368/S245 |
| Anneal | B4678/S35678 |
| 2x2 | B36/S125 |
| HighLife | B36/S23 |
| Maze | B3/S12345 |
| Move | B368/S245 |
| Replicator | B1357/S1357 |

Click a rule to apply it immediately.

---

## Command Palette

Press `Ctrl+Shift+P` to open the command palette. Type to filter available actions, then press Enter or click to execute.

---

## Population Graph

The sidebar displays a real-time chart of population over the last 500 generations. It updates automatically during simulation.

---

## Pattern Shape Search

Open the pattern shape search panel to:

1. Draw a small pattern on the mini-canvas.
2. Click **Search** to find patterns in the library that match by shape similarity.
3. Click a result to load it onto the main grid.

---

## Grid Display

| Setting | Key | Description |
|---------|-----|-------------|
| Toggle grid lines | `G` | Show or hide the cell grid |
| Zoom in | `+` | Decrease cell size |
| Zoom out | `-` | Increase cell size |

### Overlays

From the View menu:

- **Cell age heatmap** — colors cells from blue (new) to red (old)
- **Activity heatmap** — highlights areas with frequent state changes
- **Symmetry guides** — draws symmetry axes on the grid

---

## Exporting

### From the GUI

| Format | How |
|--------|-----|
| PNG snapshot | `Ctrl+S` or File → Export PNG |
| Animated GIF | File → Export GIF |
| MP4 video | File → Export MP4 |
| WebM video | File → Export WebM |
| JSON state | File → Export JSON |
| CSV statistics | File → Export CSV |

### From the CLI

```bash
python src/cli.py --mode conway --steps 500 --export output/sim.gif --fps 15
```

See [CLI Reference](cli_reference.md) for all options.

---

## Settings Persistence

LifeGrid saves your preferences (window size, grid dimensions, theme, speed, etc.) to `settings.json` in the project root. Settings are loaded automatically on startup.
