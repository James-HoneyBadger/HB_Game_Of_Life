# API Reference

LifeGrid provides a REST and WebSocket API built with FastAPI for programmatic access, streaming, and collaborative editing. Version 4 clients should use the `/api/v1` route prefix; the unprefixed routes remain available during the migration.

## Starting the Server

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API runs at `http://localhost:8000`. Interactive docs are available at `/docs` (Swagger UI) and `/redoc`.

---

## REST Endpoints

Versioned equivalents are available under `/api/v1`, for example
`GET /api/v1/modes`, `GET /api/v1/patterns?mode=conway`, and `POST /api/v1/session`. Versioned WebSocket routes
include `/api/v1/session/{id}/stream` and `/api/v1/collab/{id}`.

### Health Check

```
GET /health
```

**Response:** `{"status": "ok"}`

---

### Diagnostics

```
GET /diagnostics
```

Returns runtime version, Python/platform information, mode/plugin counts,
pattern-resource status, and active session capacity. The same endpoint is
available under `/api/v1/diagnostics`.

---

### Mode Discovery

```
GET /modes
```

Returns canonical automaton names, descriptions, and accepted aliases so API
clients can build mode selectors without duplicating the registry.

**Response:**

```json
[
  {
    "name": "Conway's Game of Life",
    "description": "Classic B3/S23 cellular automaton",
    "aliases": ["conway"],
    "source": "builtin",
    "api_version": 1,
    "capabilities": {}
  }
]
```

---

### Boundary Modes

LifeGrid supports three canonical boundary modes for simulation edges:

- `wrap` (also accepted as `toroidal`, `wrap-around`, `wrap_around`, `continuous`, `loop`, `wrapped`) — cells crossing the edge reappear on the opposite side and continue moving normally.
- `fixed` — cells outside the grid are treated as dead.
- `reflect` — the edge mirrors the grid interior.

This behavior is implemented in the simulator core and is available to both the GUI and the API.

---

### Boundary Discovery

```
GET /boundaries
```

Returns the canonical boundary modes and accepted aliases for client and UI discovery.

**Response:**

```json
[
  {
    "name": "wrap",
    "description": "Toroidal wraparound: cells continue across opposite edges",
    "aliases": ["toroidal", "wrap-around", "continuous", "loop"],
    "api_version": 1,
    "capabilities": {"cross_boundary_motion": true}
  }
]
```

---

### Create Session

```
POST /session
```

Creates a new simulation session.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | int (4–2048) | 64 | Grid width |
| `height` | int (4–2048) | 64 | Grid height |
| `mode` | string | `"conway"` | Automaton mode or alias |
| `boundary_mode` | string | `"wrap"` | Boundary mode: `wrap` (aliases: `toroidal`, `wrap-around`, `continuous`, `loop`), `fixed`, or `reflect` |
| `seed` | int (non-negative) | null | Seed for reproducible procedural patterns |
| `max_cycle_states` | int (1–1,000,000) | 10000 | Cycle fingerprint memory limit |
| `birth_rule` | string | null | Custom birth counts, e.g. `"36"` |
| `survival_rule` | string | null | Custom survival counts, e.g. `"23"` |
| `pattern` | string | null | Pattern name to load |

**Response:** `{"session_id": "<uuid>"}`

**Example:**

```bash
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"width": 128, "height": 128, "mode": "highlife", "boundary_mode": "fixed"}'
```

---

### Delete Session

```
DELETE /session/{session_id}
```

Deletes the in-memory session.

**Response:** `{"status": "deleted"}`

---

### Restore Session

```
POST /session/restore
```

Creates a new session from the JSON object returned by
`GET /session/{session_id}/snapshot`.

**Response:** `{"session_id": "<uuid>"}`

Invalid or unsupported snapshots return HTTP 400.

The process-local service enforces `LIFEGRID_MAX_SESSIONS` (default `100`).
Creation returns HTTP 503 when capacity is reached.

---

### List Sessions

```
GET /sessions
```

Returns active in-memory sessions with canonical mode, boundary, seed, and
generation metadata.

---

### Get Session Metadata

```
GET /session/{session_id}
```

Returns one session's configuration and aggregate metrics without returning the
full grid.

---

### Step Session

```
POST /session/{session_id}/step
```

Advance the simulation by one or more generations.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `steps` | int (1–1000) | 1 | Number of generations to advance |

**Response:** `{"generation": <int>}`

---

### Reset Session

```
POST /session/{session_id}/reset
```

Clears the current automaton and resets generation and metrics.

**Response:** `{"generation": 0}`

---

### Get State

```
GET /session/{session_id}/state
```

Returns the current grid state.

The API returns raw simulation state. Renderer-only overlays, such as the
Langton's Ant marker used by the GUI, are not included.

**Response:**

```json
{
  "generation": 42,
  "width": 128,
  "height": 128,
  "grid": [[0, 1, 0, ...], ...]
}
```

---

### Get Snapshot

```
GET /session/{session_id}/snapshot
```

Returns a versioned JSON snapshot containing configuration, grid, generation,
metrics, and RNG state for replay or persistence.

---

### Get Metrics

```
GET /session/{session_id}/metrics
```

Returns aggregate metrics including generation count, population, density,
undo/redo availability, and cycle-detection status.

**Response example:**

```json
{
  "generations": 10,
  "current_population": 24,
  "max_population": 31,
  "avg_density": 0.0064,
  "births": 12,
  "deaths": 8,
  "state_counts": {"0": 9976, "1": 24},
  "undo_available": true,
  "redo_available": false,
  "cycle_detected": false,
  "cycle_start": null,
  "cycle_period": null
}
```

---

### Load Pattern

```
POST /session/{session_id}/pattern
```

Load a pattern into the session grid.

**Request body:**

| Field | Type | Description |
|-------|------|-------------|
| `rle` | string | RLE-encoded pattern string |
| `pattern_name` | string | Named pattern to load |

Provide either `rle` or `pattern_name`.

Mode aliases are case-insensitive. For example, `conway`, `highlife`, and
`hexagonal` are accepted alongside their canonical display names. Unknown
modes and incomplete custom-rule pairs return HTTP 400.

**Response:** `{"status": "ok"}`

---

### Errors

All endpoints return `404` if the session ID is unknown.

---

## WebSocket Endpoints

### Simulation Stream

```
WS /session/{session_id}/stream
```

Connects to a simulation session and receives grid state frames automatically at approximately 20 Hz. Each frame is a JSON message with the same schema as the `GET /session/{id}/state` response.

**Example (Python):**

```python
import asyncio
import websockets
import json

async def stream():
    async with websockets.connect("ws://localhost:8000/session/<id>/stream") as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Generation {data['generation']}, grid {data['width']}x{data['height']}")

asyncio.run(stream())
```

---

### Collaborative Session

```
WS /collab/{session_id}?width=<int>&height=<int>
```

Multi-user collaborative editing. Multiple WebSocket clients share the same grid. The grid is created on demand with the specified dimensions (default 64x64).

**Actions (client → server):**

| Action | Payload | Description |
|--------|---------|-------------|
| `draw` | `{"x": int, "y": int, "value": int}` | Set a cell |
| `clear` | — | Clear the grid and reset generation |
| `step` | — | Advance one Conway generation |
| `start` | — | Begin auto-stepping |
| `stop` | — | Stop auto-stepping |
| `set_speed` | `{"delay": float}` | Set seconds between auto-steps (min 0.02) |

**Message format (client → server):**

```json
{"action": "draw", "x": 10, "y": 15, "value": 1}
```

**Broadcasts (server → all clients):**

After every mutation the server broadcasts the full grid state to all connected clients:

```json
{
  "type": "state",
  "generation": 5,
  "grid": [[0, 1, ...], ...]
}
```

**Example (Python):**

```python
import asyncio
import websockets
import json

async def collab():
    uri = "ws://localhost:8000/collab/my-room?width=32&height=32"
    async with websockets.connect(uri) as ws:
        # Draw a cell
        await ws.send(json.dumps({"action": "draw", "x": 5, "y": 5, "value": 1}))
        # Receive broadcast
        state = json.loads(await ws.recv())
        print(f"Generation: {state['generation']}")

asyncio.run(collab())
```

---

## Core Python API

### Simulator

```python
from src.core.config import SimulatorConfig
from src.core.simulator import Simulator

config = SimulatorConfig(width=100, height=100, automaton_mode="Conway's Game of Life")
sim = Simulator(config)

sim.initialize()
metrics = sim.step(num_steps=10)       # Returns list of {generation, population, density}
grid = sim.get_grid()                   # numpy.ndarray
sim.set_cell(50, 50, 1)
sim.undo()
sim.redo()
summary = sim.get_metrics_summary()     # {generations, current_population, max_population, ...}
```

### Export Manager

```python
from src.export_manager import ExportManager

em = ExportManager()

# Single image
em.export_png(grid, "snapshot.png", cell_size=8)

# Animated GIF
for frame in frames:
    em.add_frame(frame)
em.export_gif("animation.gif", cell_size=8, duration=100)

# Video
em.export_video("video.mp4", cell_size=8, fps=10)

# JSON
em.export_json("state.json", grid, metadata={"generation": 100})
```

### RLE Parser

```python
from src.advanced.rle_format import RLEParser, RLEEncoder

# Parse
grid, metadata = RLEParser.parse("bo$2bo$3o!")
grid, metadata = RLEParser.parse_file("pattern.rle")

# Encode
rle_string = RLEEncoder.encode(grid)
RLEEncoder.encode_to_file(grid, "output.rle")
```

### Plugin System

```python
from plugin_system import PluginManager

pm = PluginManager()
count = pm.load_plugins_from_directory("plugins")
print(pm.list_plugins())  # ["Day & Night"]

automaton = pm.create_automaton("Day & Night", 100, 100)
```
