# Contributing to LifeGrid

Thanks for your interest in contributing! This guide covers setup, workflow, and standards.

---

## Development Setup

```bash
git clone https://github.com/James-HoneyBadger/LifeGrid.git
cd LifeGrid
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev,docs,export]"
```

This installs all dependencies (runtime, dev, docs, export) in editable mode.

New public imports should use the Version 4 namespace, for example
`from lifegrid.core.simulator import Simulator`. The older top-level imports
remain implementation details during the migration.

### Prerequisites

- Python 3.11+
- Tcl/Tk
- Git

---

## Workflow

1. **Fork and clone** the repository.
2. **Create a branch** from `master`:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Make your changes** — keep commits focused and well-described.
4. **Run the checks** before submitting:
   ```bash
    .venv/bin/python -m pytest -q
    .venv/bin/python -m py_compile src/cli.py src/core/simulator.py
    git diff --check
   ```
5. **Open a pull request** against `master`.

---

## Code Standards

- **Style**: PEP 8. Use the configured Black and isort tools when making formatting changes.
- **Type hints**: All public functions and methods should have type annotations. Run mypy when changing typed public APIs.
- **Linting**: Zero warnings from `flake8` and zero errors from `pylint --errors-only`.
- **Tests**: New features should include tests in `tests/`. Run `.venv/bin/python -m pytest -q`.
- **Docstrings**: Use Google-style docstrings for public APIs.

---

## Adding An Automaton Mode

### As a plugin (recommended)

Create a `.py` file in `plugins/` that subclasses `AutomatonPlugin`:

```python
from plugin_system import AutomatonPlugin
from automata.base import CellularAutomaton

class MyPlugin(AutomatonPlugin):
    @property
    def name(self) -> str:
        return "My Automaton"

    @property
    def description(self) -> str:
        return "Description of the rules"

    @property
    def version(self) -> str:
        return "1.0"

    def create_automaton(self, width: int, height: int) -> CellularAutomaton:
        # Return your automaton instance
        ...
```

Plugins are auto-discovered at startup — no code changes to the core required.

### As a built-in mode

1. Create a new file in `src/automata/` subclassing `CellularAutomaton`.
2. Export it from `src/automata/__init__.py`.
3. Register it in `src/gui/config.py` (`MODE_FACTORIES` and `MODE_PATTERNS`).
4. Add patterns to `src/data/patterns.json` or the appropriate automaton's procedural loader.
5. Add a CLI alias in `src/cli.py`.
6. Write tests.

## Release Checklist

For a release such as `3.2.1`:

1. Update the version in `src/version.py` and `[project].version` in `pyproject.toml`.
2. Update the README badge and the technical reference version.
3. Add a dated entry to `CHANGELOG.md`.
4. Run the full test suite, package build, and `git diff --check`:
    ```bash
    .venv/bin/python -m pytest -q
    .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /tmp/lifegrid-wheel .
    git diff --check
    ```
5. Inspect the wheel for `data/patterns.json`.
6. Create the release commit and version tag only after the checks pass.

---

## Project Layout

| Directory | Purpose |
|-----------|---------|
| `src/automata/` | Automaton implementations |
| `src/core/` | Simulator engine, config, undo, boundary |
| `src/gui/` | GUI application and widgets |
| `src/api/` | FastAPI REST + WebSocket server |
| `src/advanced/` | Statistics, analysis, RLE, heatmaps |
| `src/performance/` | GPU acceleration, benchmarking |
| `plugins/` | User-installable plugins |
| `tests/` | Test suite |
| `docs/` | Documentation |
| `examples/` | Example scripts |

---

## Reporting Issues

Open a GitHub issue with:

- A clear title and description
- Steps to reproduce (if it's a bug)
- Expected vs. actual behavior
- Python version and OS

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
