# Architecture

This document describes LifeGrid's internal architecture and module relationships.

---

## High-Level Overview

```
┌──────────────────────────────────────────────────┐
│                  Entry Points                    │
│  main.py (GUI)   cli.py (CLI)   api/app.py (API) │
└──────┬──────────────┬──────────────┬─────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────────────────────────────────────────────┐
│               Core Engine Layer                  │
│  Simulator  ←→  SimulatorConfig                  │
│      │                                           │
│      ├── UndoManager      (state history)        │
│      ├── BoundaryMode     (wrap/fixed/reflect)   │
│      └── CellularAutomaton (abstract base)       │
└──────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────┐
│             Automata Implementations             │
│  ConwayGameOfLife  │  HighLife  │  Wireworld     │
│  BriansBrain       │  LangtonsAnt │ Generations  │
│  ImmigrationGame   │  RainbowGame │ HexagonalGoL │
│  LifeLikeAutomaton (custom B/S rules)            │
└──────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────┐
│              Support Modules                     │
│  ExportManager    │  PatternManager              │
│  PluginManager    │  ConfigManager (AppConfig)   │
│  ThemeManager     │  StatisticsCollector          │
│  EnhancedStatistics │ PatternAnalyzer            │
│  RLEParser/Encoder  │ CellAgeTracker             │
│  HeatmapGenerator   │ SymmetryAnalyzer           │
│  RuleDiscovery      │ GPUSimulator               │
└──────────────────────────────────────────────────┘
```

---

## Module Breakdown

### Entry Points

| Module | Purpose |
|--------|---------|
| `src/main.py` | Launches the Tkinter GUI via `AutomatonApp` |
| `src/cli.py` | Headless CLI with argparse. Creates a `Simulator`, runs N steps, exports results. |
| `src/api/app.py` | FastAPI server with REST endpoints and WebSocket streams |

### Core (`src/core/`)

| Module | Key Classes | Responsibility |
|--------|-------------|----------------|
| `simulator.py` | `Simulator` | Orchestrates automaton stepping, undo/redo, metrics, callbacks |
| `config.py` | `SimulatorConfig` | Dataclass holding grid size, speed, mode, rule sets, feature flags |
| `undo_manager.py` | `UndoManager` | Bounded stack of grid snapshots (default 100) |
| `boundary.py` | `BoundaryMode`, `convolve_with_boundary()`, `roll_with_boundary()` | Edge-handling strategies |
| `utils.py` | Utility functions | Shared helpers |

The `Simulator` owns a `CellularAutomaton` instance and an `UndoManager`. On each `step()` call it:

1. Pushes the current grid to the undo stack.
2. Calls `automaton.step()`.
3. Records metrics (generation, population, density).
4. Fires the on-step callback.

### Automata (`src/automata/`)

All automata inherit from `CellularAutomaton` (defined in `base.py`) which requires:

- `step()` — advance one generation
- `get_grid() -> np.ndarray` — return the current grid
- `set_cell(x, y, value)` — set a cell value
- `reset()` — clear the grid

Each implementation uses `scipy.signal.convolve2d` (or manual convolution for hexagonal/ant) to compute the next generation.

`LifeLikeAutomaton` accepts arbitrary B/S rules via `parse_bs()`, making it the backbone of custom-rule support and the Rule Explorer.

### GUI (`src/gui/`)

| Module | Purpose |
|--------|---------|
| `app.py` | `AutomatonApp` — main window, menus, toolbar, event loop |
| `rendering.py` | Canvas drawing: cells, grid lines, overlays |
| `ui.py` | UI builder: creates widgets, binds callbacks |
| `config.py` | GUI constants: `MODE_FACTORIES`, `MODE_PATTERNS`, colors |
| `state.py` | `SimulationState` — mutable runtime state (grid, speed, history deques) |
| `tools.py` | `ToolManager` — pencil/eraser/stamp/selection, brush settings |
| `new_features.py` | `GenerationTimeline`, `PopulationGraph`, `BreakpointManager`, `RuleExplorer`, `CommandPalette`, `ThemeEditorDialog`, `PatternShapeSearch` |
| `enhanced_features.py` | Additional feature widgets |
| `enhanced_rendering.py` | Enhanced rendering utilities |
| `icon_factory.py` | Procedural icon generation |
| `layouts.py` | Layout management helpers |
| `modern_ui.py` | Modern UI components (styled buttons, frames) |
| `ui_polish.py` | Visual refinements |

The GUI uses Tkinter's `grid` geometry manager throughout. The main layout is:

```
root
└── content_frame (grid)
    ├── toolbar (row 0, sticky EW)
    ├── sidebar (row 1, column 0)
    ├── canvas  (row 1, column 1)
    ├── timeline (row 2, columnspan 2)
    ├── graph   (row 3, columnspan 2)
    └── statusbar (row 4, columnspan 2)
```

### API (`src/api/`)

| Module | Purpose |
|--------|---------|
| `app.py` | FastAPI application with session CRUD, stepping, state retrieval, pattern loading, WebSocket streaming |
| `collab.py` | `CollaborativeSession` — multi-client shared grid with asyncio lock |

Sessions are stored in a module-level dict keyed by UUID. The collaborative endpoint creates sessions on demand.

### Advanced Analytics (`src/advanced/`)

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| `statistics.py` | `StatisticsCollector`, `StatisticsExporter` | Per-generation metrics collection, CSV/plot export |
| `enhanced_statistics.py` | `EnhancedStatistics` | Entropy, complexity, fractal dimension, connected components, cluster stats, symmetry, center of mass, radial distribution |
| `pattern_analysis.py` | `PatternAnalyzer` | Bounding box, period detection, displacement detection |
| `pattern_manager.py` | `PatternManager` | Favorites/history backed by JSON, tag-based search, similarity matching |
| `rle_format.py` | `RLEParser`, `RLEEncoder` | Run-Length Encoded pattern format I/O |
| `rule_discovery.py` | `RuleDiscovery` | Observe cell transitions, infer B/S rules, export |
| `cell_tracker.py` | `CellAgeTracker`, `CellHistoryTracker` | Track cell age, birth/death history |
| `visualization.py` | `HeatmapGenerator`, `SymmetryAnalyzer` | Activity/age heatmaps, symmetry detection and scoring |

### Performance (`src/performance/`)

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| `gpu.py` | `GPUSimulator`, `xp` backend | CuPy-accelerated Life-like simulation with NumPy fallback |
| `benchmarking.py` | Benchmarking utilities | Performance measurement and reporting |

### Plugin System (`src/plugin_system.py`)

`PluginManager` scans a directory for `.py` files, imports them, finds `AutomatonPlugin` subclasses, and registers them. Plugins are discovered at GUI startup from the `plugins/` directory.

### Export (`src/export_manager.py`)

`ExportManager` handles all output formats (PNG, GIF, MP4, WebM, JSON). It accumulates frames for animation export and supports 4 color themes (light, dark, blue, warm).

### Configuration

| Module | Class | Storage |
|--------|-------|---------|
| `src/core/config.py` | `SimulatorConfig` | In-memory dataclass |
| `src/config_manager.py` | `AppConfig` | Persisted to `settings.json` |

---

## Data Flow

### GUI Simulation Loop

```
User clicks Start
    → AutomatonApp sets running = True
    → Tkinter after() callback fires every (101 - speed) ms
        → Simulator.step()
            → UndoManager.push_state(grid)
            → CellularAutomaton.step()
            → Metrics recorded
            → on_step callback fires
        → Canvas re-rendered
        → Timeline updated
        → PopulationGraph updated
        → Breakpoints checked
```

### CLI Pipeline

```
argparse → build SimulatorConfig → Simulator.initialize()
    → loop N steps, collecting frames
    → ExportManager.export_*(frames, output_path)
```

### API Request Flow

```
HTTP POST /session → create Simulator → store in sessions dict → return UUID
HTTP POST /session/{id}/step → lookup Simulator → step() → return generation
WS /session/{id}/stream → lookup Simulator → loop: step + send JSON state
WS /collab/{id} → lookup or create CollaborativeSession → broadcast mutations
```
