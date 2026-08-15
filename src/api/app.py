"""FastAPI service scaffold for LifeGrid.

Exposes endpoints for session management, stepping, pattern loading,
and streaming. Wraps the core Simulator for HTTP and WebSocket clients.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from fastapi import APIRouter, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from advanced.rle_format import RLEParser
from core.config import SimulatorConfig
from core.utils import place_pattern_centered
from core.simulator import Simulator
from core.registry import iter_modes, normalize_mode
from core.boundary import BOUNDARY_ALIASES, BoundaryMode
from core.snapshot import load_snapshot_dict, snapshot_dict
from plugin_system import PluginManager
from patterns import PATTERN_DATA
from version import __version__
from .collab import collab_websocket_handler

app = FastAPI(title="LifeGrid API", version="1.0.0")
v1_router = APIRouter()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class SessionState:
    """Holds the state for a single simulation session."""

    simulator: Simulator
    session_id: str
    last_grid: Optional[np.ndarray] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    """Request schema for creating a new session."""

    width: int = Field(64, ge=4, le=2048)
    height: int = Field(64, ge=4, le=2048)
    mode: str = "Conway's Game of Life"
    boundary_mode: str = "wrap"
    seed: Optional[int] = Field(None, ge=0)
    max_cycle_states: int = Field(10000, ge=1, le=1_000_000)
    birth_rule: Optional[str] = None
    survival_rule: Optional[str] = None
    pattern: Optional[str] = None


class StepRequest(BaseModel):
    """Request schema for stepping the simulation."""

    steps: int = Field(1, ge=1, le=1000)


class PatternRequest(BaseModel):
    """Request schema for applying a pattern."""

    rle: Optional[str] = None
    pattern_name: Optional[str] = None


_sessions: Dict[str, SessionState] = {}
try:
    MAX_SESSIONS = max(1, int(os.getenv("LIFEGRID_MAX_SESSIONS", "100")))
except ValueError:
    MAX_SESSIONS = 100
_plugin_manager = PluginManager()
_plugin_directory = Path.cwd() / "plugins"
if _plugin_directory.is_dir():
    _plugin_manager.load_plugins_from_directory(str(_plugin_directory))

def _resolve_mode(name: str) -> str:
    """Resolve a case-insensitive API mode alias."""
    return normalize_mode(name)


def _parse_rule(rule: Optional[str]) -> Optional[set[int]]:
    """Convert a rule string like "23" into a set of ints {2, 3}."""
    if rule is None:
        return None
    digits = [int(ch) for ch in rule if ch.isdigit()]
    return set(digits)


def _get_session(session_id: str) -> SessionState:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/diagnostics")
def diagnostics() -> dict[str, object]:
    """Return service runtime and resource diagnostics."""
    return {
        "status": "ok",
        "lifegrid_version": __version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "mode_count": len(list_modes()),
        "plugin_count": sum(
            1 for descriptor in iter_modes() if descriptor.source == "plugin"
        ),
        "patterns_available": bool(PATTERN_DATA),
        "active_sessions": len(_sessions),
        "max_sessions": MAX_SESSIONS,
    }


@app.get("/modes")
def list_modes() -> list[dict[str, object]]:
    """List canonical modes, descriptions, and accepted aliases."""
    return [
        {
            "name": descriptor.name,
            "description": descriptor.description,
            "aliases": list(descriptor.aliases),
            "state_count": descriptor.state_count,
            "supports_patterns": descriptor.supports_patterns,
                    "source": descriptor.source,
                    "api_version": descriptor.api_version,
                    "capabilities": descriptor.capabilities,
        }
        for descriptor in iter_modes()
    ]


@app.get("/patterns")
def list_patterns(mode: str = "Conway's Game of Life") -> list[dict[str, str]]:
    """List named pattern metadata for a canonical mode or alias."""
    try:
        canonical_mode = _resolve_mode(mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    patterns = PATTERN_DATA.get(canonical_mode, {})
    return [
        {"name": name, "description": description}
        for name, (_, description) in patterns.items()
    ]


@app.get("/boundaries")
def list_boundaries() -> list[dict[str, object]]:
    """List canonical boundary modes and the aliases accepted by the parser."""
    payload = []
    for member in BoundaryMode:
        aliases = BOUNDARY_ALIASES.get(member.value, [])
        payload.append(
            {
                "name": member.value,
                "description": {
                    BoundaryMode.WRAP: "Toroidal wraparound: cells continue across opposite edges",
                    BoundaryMode.FIXED: "Cells outside the grid are treated as dead",
                    BoundaryMode.REFLECT: "Edges mirror the grid interior before continuing",
                }[member],
                "aliases": aliases,
                "api_version": 1,
                "capabilities": {
                    "cross_boundary_motion": member is BoundaryMode.WRAP,
                },
            }
        )
    return payload


@app.post("/session")
def create_session(req: CreateSessionRequest) -> Dict[str, str]:
    """Create and initialize a new simulation session."""
    session_id = str(uuid.uuid4())
    if len(_sessions) >= MAX_SESSIONS:
        raise HTTPException(status_code=503, detail="Session capacity reached")
    if (req.birth_rule is None) != (req.survival_rule is None):
        raise HTTPException(
            status_code=400,
            detail="birth_rule and survival_rule must be provided together",
        )
    try:
        mode = _resolve_mode(req.mode)
        boundary_mode = BoundaryMode.from_string(req.boundary_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    config = SimulatorConfig(
        width=req.width,
        height=req.height,
        automaton_mode=mode,
        birth_rule=_parse_rule(req.birth_rule),
        survival_rule=_parse_rule(req.survival_rule),
        boundary_mode=boundary_mode,
        seed=req.seed,
        max_cycle_states=req.max_cycle_states,
    )
    sim = Simulator(config)
    try:
        sim.initialize(mode=mode, pattern=req.pattern)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _sessions[session_id] = SessionState(simulator=sim, session_id=session_id)
    return {"session_id": session_id}


@app.get("/sessions")
def list_sessions() -> list[dict[str, object]]:
    """List active in-memory simulation sessions and basic metadata."""
    return [
        {
            "session_id": session_id,
            "mode": session.simulator.config.automaton_mode,
            "boundary_mode": session.simulator.config.boundary_mode.value,
            "seed": session.simulator.config.seed,
            "max_cycle_states": session.simulator.config.max_cycle_states,
            "generation": session.simulator.generation,
        }
        for session_id, session in _sessions.items()
    ]


@app.get("/session/{session_id}")
def get_session(session_id: str) -> dict[str, object]:
    """Return metadata for one active session without its grid."""
    session = _get_session(session_id)
    summary = session.simulator.get_metrics_summary()
    return {
        "session_id": session_id,
        "mode": session.simulator.config.automaton_mode,
        "boundary_mode": session.simulator.config.boundary_mode.value,
        "seed": session.simulator.config.seed,
        "generation": session.simulator.generation,
        "estimated_memory_bytes": session.simulator.estimate_memory_bytes(),
        "metrics": summary,
    }


@app.post("/session/restore")
def restore_session(payload: dict) -> Dict[str, str]:
    """Create a new session from a versioned simulator snapshot."""
    if len(_sessions) >= MAX_SESSIONS:
        raise HTTPException(status_code=503, detail="Session capacity reached")
    try:
        simulator = load_snapshot_dict(payload)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session_id = str(uuid.uuid4())
    _sessions[session_id] = SessionState(
        simulator=simulator, session_id=session_id
    )
    return {"session_id": session_id}


@app.delete("/session/{session_id}")
def delete_session(session_id: str) -> Dict[str, str]:
    """Delete a simulation session and release its in-memory state."""
    if _sessions.pop(session_id, None) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@app.post("/session/{session_id}/step")
def step_session(session_id: str, req: StepRequest) -> Dict[str, int]:
    """Advance the simulation by a number of steps."""
    session = _get_session(session_id)
    session.simulator.step(req.steps)
    session.last_grid = session.simulator.get_raw_grid()
    return {"generation": int(session.simulator.generation)}


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str) -> Dict[str, int]:
    """Reset a session to its current automaton's empty state."""
    session = _get_session(session_id)
    session.simulator.reset()
    return {"generation": int(session.simulator.generation)}


@app.get("/session/{session_id}/state")
def get_state(session_id: str) -> Dict[str, object]:
    """Retrieve the current grid state and generation."""
    session = _get_session(session_id)
    grid = session.simulator.get_raw_grid()
    session.last_grid = grid
    return {
        "generation": int(session.simulator.generation),
        "width": int(grid.shape[1]),
        "height": int(grid.shape[0]),
        "boundary_mode": session.simulator.config.boundary_mode.value,
        "seed": session.simulator.config.seed,
        "grid": grid.astype(int).tolist(),
    }


@app.get("/session/{session_id}/snapshot")
def get_snapshot(session_id: str) -> dict:
    """Return a versioned, replayable snapshot of a session."""
    return snapshot_dict(_get_session(session_id).simulator)


@app.get("/session/{session_id}/metrics")
def get_metrics(session_id: str) -> dict:
    """Return aggregate metrics for a simulation session."""
    session = _get_session(session_id)
    return session.simulator.get_metrics_summary()


@app.post("/session/{session_id}/pattern")
def load_pattern(session_id: str, req: PatternRequest) -> Dict[str, str]:
    """Load a pattern (RLE or named) into the grid."""
    session = _get_session(session_id)
    if session.simulator.automaton is None:
        raise HTTPException(
            status_code=500,
            detail="Simulator not initialized",
        )

    if req.rle and req.pattern_name:
        raise HTTPException(
            status_code=400,
            detail="Provide either rle or pattern_name, not both",
        )

    if req.rle:
        try:
            pattern, _ = RLEParser.parse(req.rle)

            # Create new grid with session dimensions
            current_grid = session.simulator.get_raw_grid()
            h, w = current_grid.shape
            # Create new grid and place pattern
            new_grid = np.zeros((h, w), dtype=int)
            place_pattern_centered(new_grid, pattern)

            session.simulator.replace_grid(new_grid)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse RLE: {str(e)}",
            ) from e

    if req.pattern_name:
        try:
            session.simulator.load_pattern(req.pattern_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.last_grid = session.simulator.get_raw_grid()
    return {"status": "ok"}


@app.websocket("/session/{session_id}/stream")
async def stream_state(websocket: WebSocket, session_id: str) -> None:
    """Stream simulation state via WebSocket."""
    await websocket.accept()
    session = _get_session(session_id)
    try:
        while True:
            session.simulator.step()
            grid = session.simulator.get_raw_grid()
            payload = {
                "generation": int(session.simulator.generation),
                "width": int(grid.shape[1]),
                "height": int(grid.shape[0]),
                "grid": grid.astype(int).tolist(),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        return


@app.websocket("/collab/{session_id}")
async def collab_stream(
    websocket: WebSocket,
    session_id: str,
    width: int = 64,
    height: int = 64,
) -> None:
    """Collaborative multi-user simulation via WebSocket."""
    await collab_websocket_handler(websocket, session_id, width, height)


@v1_router.get("/health")
def v1_health() -> Dict[str, str]:
    return health()


@v1_router.get("/diagnostics")
def v1_diagnostics() -> dict[str, object]:
    return diagnostics()


@v1_router.get("/modes")
def v1_modes() -> list[dict[str, object]]:
    return list_modes()


@v1_router.get("/patterns")
def v1_patterns(mode: str = "Conway's Game of Life") -> list[dict[str, str]]:
    return list_patterns(mode)


@v1_router.get("/boundaries")
def v1_boundaries() -> list[dict[str, object]]:
    return list_boundaries()


@v1_router.get("/sessions")
def v1_sessions() -> list[dict[str, object]]:
    return list_sessions()


@v1_router.post("/session")
def v1_create_session(req: CreateSessionRequest) -> Dict[str, str]:
    return create_session(req)


@v1_router.post("/session/restore")
def v1_restore_session(payload: dict) -> Dict[str, str]:
    return restore_session(payload)


@v1_router.delete("/session/{session_id}")
def v1_delete_session(session_id: str) -> Dict[str, str]:
    return delete_session(session_id)


@v1_router.get("/session/{session_id}")
def v1_get_session(session_id: str) -> dict[str, object]:
    return get_session(session_id)


@v1_router.post("/session/{session_id}/step")
def v1_step_session(session_id: str, req: StepRequest) -> Dict[str, int]:
    return step_session(session_id, req)


@v1_router.post("/session/{session_id}/reset")
def v1_reset_session(session_id: str) -> Dict[str, int]:
    return reset_session(session_id)


@v1_router.get("/session/{session_id}/state")
def v1_state(session_id: str) -> Dict[str, object]:
    return get_state(session_id)


@v1_router.get("/session/{session_id}/metrics")
def v1_metrics(session_id: str) -> dict:
    return get_metrics(session_id)


@v1_router.get("/session/{session_id}/snapshot")
def v1_snapshot(session_id: str) -> dict:
    return get_snapshot(session_id)


@v1_router.post("/session/{session_id}/pattern")
def v1_pattern(session_id: str, req: PatternRequest) -> Dict[str, str]:
    return load_pattern(session_id, req)


@v1_router.websocket("/session/{session_id}/stream")
async def v1_stream(websocket: WebSocket, session_id: str) -> None:
    await stream_state(websocket, session_id)


@v1_router.websocket("/collab/{session_id}")
async def v1_collaboration(
    websocket: WebSocket,
    session_id: str,
    width: int = 64,
    height: int = 64,
) -> None:
    await collab_stream(websocket, session_id, width, height)


app.include_router(v1_router, prefix="/api/v1")
