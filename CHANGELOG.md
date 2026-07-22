# Changelog

All notable changes to LifeGrid are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] — 2025-06-17

### Added

- **Headless CLI** (`src/cli.py`) — run simulations from the command line with `--mode`, `--rule`, `--steps`, `--export`, `--fps`, `--snapshot-every`, and `--quiet` flags.
- **Boundary modes** — wrap (toroidal), fixed (dead edges), and reflect (mirror edges) via `BoundaryMode` enum and utility functions in `src/core/boundary.py`.
- **GPU acceleration** — optional CuPy-based CUDA acceleration with automatic NumPy fallback (`src/performance/gpu.py`).
- **Generation timeline** — scrub backward and forward through past simulation states in the GUI sidebar.
- **Population graph** — real-time population-over-time chart displayed below the canvas.
- **Breakpoint system** — pause the simulation when configurable conditions on population, generation, or density are met.
- **Rule explorer** — browse and apply 10 named Life-like rulesets (Seeds, Day & Night, Diamoeba, Morley, Anneal, 2x2, HighLife, Maze, Move, Replicator).
- **Command palette** — `Ctrl+Shift+P` quick-access overlay listing all available actions.
- **Theme editor** — visual in-app editor for creating and applying custom color themes with 3 built-in presets.
- **Pattern shape search** — draw a pattern on a mini-canvas and search the library by shape similarity.
- **Collaborative sessions** — WebSocket-based multi-user grid editing via `/collab/{id}` endpoint in the API.
- **Hexagonal Life** mode — hexagonal grid variant (`src/automata/hexagonal.py`).
- **Comprehensive test suite** — 71 tests in `tests/test_thorough.py` covering all major components.

### Fixed

- `Simulator.undo()` and `Simulator.redo()` now correctly pass `current_state` to `UndoManager`.
- GUI crash caused by mixing `pack` and `grid` geometry managers on the root window.
- `PopulationGraph._w` no longer shadows the internal `tk.Canvas._w` attribute.
- All flake8, mypy, and pylint issues resolved (0 warnings, 0 errors).

---

## [3.0.0] — 2025-06-01

### Added

- Modern Tkinter GUI with toolbar, status bar, and tabbed settings panel.
- 9 built-in automata modes (Conway, HighLife, Immigration, Rainbow, Langton's Ant, Wireworld, Brian's Brain, Generations, Custom Rules).
- Drawing tools: pencil, eraser, stamp, and selection with configurable brush size and shape.
- Pattern browser with built-in pattern library and RLE import/export.
- Light and dark themes via `ThemeManager`.
- Undo/redo system (up to 100 states) via `UndoManager`.
- Statistics collection: population, density, entropy, complexity scoring.
- Enhanced statistics: box-counting fractal dimension, connected components, cluster analysis, pattern symmetry detection, radial distribution.
- Pattern analysis: bounding box extraction, period detection, displacement detection.
- Cell age tracking with blue-to-red gradient heatmaps.
- Activity and age heatmaps via `HeatmapGenerator`.
- Symmetry detection and visualization (horizontal, vertical, rotational, diagonal, point).
- Rule discovery: observe transitions, infer B/S notation, export discovered rules.
- Export to PNG, GIF, MP4, WebM, JSON, and CSV.
- Plugin system for user-installable automaton modes.
- Day & Night plugin (B3678/S34678).
- REST API via FastAPI with session management and pattern loading.
- WebSocket streaming of simulation frames at ~20 Hz.
- Persistent settings via `AppConfig` and `settings.json`.
- Autosave manager for recovery.
- Makefile with targets for install, test, lint, format, build, docs, and more.

---

## [2.0.0] — 2025-04-15

### Added

- Multi-mode automata engine with a shared `CellularAutomaton` base class.
- Grid rendering with zoom, pan, and cell-size controls.
- Basic pattern loading from JSON.
- Configuration via `SimulatorConfig` dataclass.
- Initial project scaffolding with `pyproject.toml`, `setup.py`, `Makefile`.

---

## [1.0.0] — 2025-02-01

### Added

- Initial release with Conway's Game of Life simulation.
- Simple Tkinter canvas renderer.
- Start, stop, step, and reset controls.
