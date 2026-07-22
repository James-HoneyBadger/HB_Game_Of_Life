# API Reference

LifeGrid provides a REST and WebSocket API built with FastAPI for programmatic access, streaming, and collaborative editing.

## Starting the Server

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API runs at `http://localhost:8000`. Interactive docs are available at `/docs` (Swagger UI) and `/redoc`.

---

## REST Endpoints

### Health Check

```
GET /health
```

**Response:** `{"status": "ok"}`

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
| `mode` | string | `"conway"` | Automaton mode |
| `birth_rule` | list[int] | null | Custom birth rule (e.g., `[3, 6]`) |
| `survival_rule` | list[int] | null | Custom survival rule (e.g., `[2, 3]`) |
| `pattern` | string | null | Pattern name to load |

**Response:** `{"session_id": "<uuid>"}`

**Example:**

```bash
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"width": 128, "height": 128, "mode": "highlife"}'
```

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

### Get State

```
GET /session/{session_id}/state
```

Returns the current grid state.

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
width, height, grid = RLEParser.parse("bo$2bo$3o!")
grid = RLEParser.parse_file("pattern.rle")

# Encode
rle_string = RLEEncoder.encode(grid)
RLEEncoder.encode_to_file(grid, "output.rle")
```

### Plugin System

```python
from src.plugin_system import PluginManager

pm = PluginManager()
count = pm.load_plugins_from_directory("plugins")
print(pm.list_plugins())  # ["Day & Night"]

automaton = pm.create_automaton("Day & Night", 100, 100)
```
