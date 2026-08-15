# Migrating From LifeGrid 3.2.1 to 4.0

Version 4 is a breaking redesign. The 3.2.1 Python implementation remains the
reference release, but new code should use the v4 contracts and package
namespace.

## Package Imports

Use the stable namespace for new code:

```python
from lifegrid.core.simulator import Simulator
from lifegrid.core.config import SimulatorConfig
from lifegrid.automata import ConwayGameOfLife
from lifegrid.io import RLEParser, ExportManager
from lifegrid.plugins import PluginManager
```

The current migration facade keeps the existing top-level modules available
while the package is being reorganized. They should be treated as internal and
may be removed at the final v4 cutover.

## Configuration

Version 4 configurations make dimensions, boundary behavior, seeds, and cycle
memory explicit:

```python
config = SimulatorConfig(
    width=128,
    height=128,
    automaton_mode="Conway's Game of Life",
    boundary_mode="fixed",
    seed=1234,
    max_cycle_states=10000,
)
```

Boundary values are `wrap`, `fixed`, and `reflect`. Random pattern generation
is owned by each simulator's random generator, so independent simulations no
longer interfere through global NumPy state.

## CLI Changes

Existing commands continue to work during migration. New controls include:

```bash
lifegrid --boundary fixed --seed 1234
lifegrid --stop-on-cycle --max-cycle-states 5000
lifegrid --snapshot output/run.lifegrid.json
lifegrid --load-snapshot output/run.lifegrid.json --steps 100
lifegrid --diagnostics
```

JSON exports now include boundary, seed, stop reason, and cycle metadata when
available. Use `--snapshot` for a complete replayable simulator state rather
than a final-grid-only JSON export.

## API Changes

Versioned routes are available under `/api/v1`:

```text
GET  /api/v1/modes
POST /api/v1/session
GET  /api/v1/sessions
POST /api/v1/session/{id}/step
POST /api/v1/session/{id}/reset
GET  /api/v1/session/{id}/state
GET  /api/v1/session/{id}/metrics
GET  /api/v1/session/{id}/snapshot
POST /api/v1/session/restore
DELETE /api/v1/session/{id}
WS   /api/v1/session/{id}/stream
WS   /api/v1/collab/{id}
```

Session creation accepts `boundary_mode`, `seed`, and `max_cycle_states`.
`GET /modes` returns canonical names, aliases, state counts, source, and API
version metadata. Unprefixed routes are migration aliases only.

## Snapshots

Snapshots are versioned JSON objects with:

- `snapshot_version`
- Simulator configuration
- Grid state
- Generation
- Metrics history
- RNG state

Use `core.snapshot.save_snapshot()` and `load_snapshot()` for files, or the API
snapshot endpoints for service sessions. Do not treat the snapshot schema as
an arbitrary JSON grid format; use RLE or the ordinary JSON export for simpler
interchange.

## Plugins

Plugins remain Python modules in `plugins/`, but their descriptors are now
registered in the canonical mode registry. Plugin modes are available to the
CLI and API as well as the GUI. Plugins should declare:

```python
api_version = 1
capabilities = {
    "patterns": True,
    "boundaries": True,
    "multi_state": False,
}
```

Plugin mode discovery is available from `/api/v1/modes`.

## Automaton Contract

Automata should implement the shared base contract:

- `reset()`
- `step()`
- `get_grid()`
- `handle_click(x, y)`
- `set_cell(x, y, value)`
- `load_pattern(name)`
- `get_state_count()`
- `set_boundary_mode(mode)`
- `set_rng(generator)`

Unknown patterns should raise an explicit error instead of silently producing
an empty grid.

## Release Checklist

Before declaring a v4 release:

1. Replace migration facade imports with the final package implementation.
2. Remove or deprecate unprefixed API routes.
3. Validate all built-in and plugin modes through the registry.
4. Build and install a clean wheel and source distribution.
5. Verify bundled pattern resources and plugin discovery.
6. Run the complete unit, integration, GUI, API, and packaging test suites.
7. Update package/runtime version to `4.0.0` and publish release notes.
