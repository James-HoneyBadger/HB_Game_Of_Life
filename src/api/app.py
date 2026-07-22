"""FastAPI service scaffold for LifeGrid.

Exposes endpoints for session management, stepping, pattern loading,
and streaming. Wraps the core Simulator for HTTP and WebSocket clients.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from advanced.rle_format import RLEParser
from core.config import SimulatorConfig
from core.utils import place_pattern_centered
from core.simulator import Simulator
from .collab import collab_websocket_handler

app = FastAPI(title="LifeGrid API", version="0.1.0")
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


@app.post("/session")
def create_session(req: CreateSessionRequest) -> Dict[str, str]:
    """Create and initialize a new simulation session."""
    session_id = str(uuid.uuid4())
    config = SimulatorConfig(
        width=req.width,
        height=req.height,
        automaton_mode=req.mode,
        birth_rule=_parse_rule(req.birth_rule),
        survival_rule=_parse_rule(req.survival_rule),
    )
    sim = Simulator(config)
    sim.initialize(mode=req.mode, pattern=req.pattern)
    _sessions[session_id] = SessionState(simulator=sim, session_id=session_id)
    return {"session_id": session_id}


@app.post("/session/{session_id}/step")
def step_session(session_id: str, req: StepRequest) -> Dict[str, int]:
    """Advance the simulation by a number of steps."""
    session = _get_session(session_id)
    session.simulator.step(req.steps)
    session.last_grid = session.simulator.get_grid()
    return {"generation": int(session.simulator.generation)}


@app.get("/session/{session_id}/state")
def get_state(session_id: str) -> Dict[str, object]:
    """Retrieve the current grid state and generation."""
    session = _get_session(session_id)
    grid = session.simulator.get_grid()
    session.last_grid = grid
    return {
        "generation": int(session.simulator.generation),
        "width": int(grid.shape[1]),
        "height": int(grid.shape[0]),
        "grid": grid.astype(int).tolist(),
    }


@app.post("/session/{session_id}/pattern")
def load_pattern(session_id: str, req: PatternRequest) -> Dict[str, str]:
    """Load a pattern (RLE or named) into the grid."""
    session = _get_session(session_id)
    if session.simulator.automaton is None:
        raise HTTPException(
            status_code=500,
            detail="Simulator not initialized",
        )

    if req.rle:
        try:
            pattern, _ = RLEParser.parse(req.rle)

            # Create new grid with session dimensions
            current_grid = session.simulator.automaton.grid
            h, w = current_grid.shape
            # Create new grid and place pattern
            new_grid = np.zeros((h, w), dtype=int)
            place_pattern_centered(new_grid, pattern)

            session.simulator.automaton.grid = new_grid

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse RLE: {str(e)}",
            ) from e

    if req.pattern_name and hasattr(
        session.simulator.automaton, "load_pattern"
    ):
        session.simulator.automaton.load_pattern(req.pattern_name)
    session.last_grid = session.simulator.get_grid()
    return {"status": "ok"}


@app.websocket("/session/{session_id}/stream")
async def stream_state(websocket: WebSocket, session_id: str) -> None:
    """Stream simulation state via WebSocket."""
    await websocket.accept()
    session = _get_session(session_id)
    try:
        while True:
            session.simulator.step()
            grid = session.simulator.get_grid()
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
