"""Collaborative real-time simulation over WebSocket.

Multiple clients connect to a shared session and can draw on the same
grid simultaneously.  Grid state is broadcast to all connected clients
after each mutation.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect


@dataclass
class CollaborativeSession:
    """State for a collaborative (multi-user) simulation session."""

    grid: np.ndarray
    generation: int = 0
    running: bool = False
    speed: float = 0.1  # seconds between auto-steps
    clients: List[WebSocket] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    async def add_client(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.append(ws)
        await self._send_state(ws)

    def remove_client(self, ws: WebSocket) -> None:
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self) -> None:
        """Send current state to all connected clients."""
        payload = self._state_payload()
        dead: list[WebSocket] = []
        for ws in self.clients:
            try:
                await ws.send_json(payload)
            except (ConnectionError, RuntimeError):
                dead.append(ws)
        for ws in dead:
            self.remove_client(ws)

    async def _send_state(self, ws: WebSocket) -> None:
        try:
            await ws.send_json(self._state_payload())
        except (ConnectionError, RuntimeError):
            pass

    def _state_payload(self) -> dict:
        return {
            "type": "state",
            "generation": self.generation,
            "width": int(self.grid.shape[1]),
            "height": int(self.grid.shape[0]),
            "grid": self.grid.astype(int).tolist(),
            "running": self.running,
        }

    async def handle_message(
        self, _ws: WebSocket, data: dict,
    ) -> None:
        """Process an incoming client message."""
        action = data.get("action")

        async with self._lock:
            if action == "draw":
                x = data.get("x", 0)
                y = data.get("y", 0)
                value = data.get("value", 1)
                h, w = self.grid.shape
                if 0 <= x < w and 0 <= y < h:
                    self.grid[y, x] = value

            elif action == "clear":
                self.grid[:] = 0
                self.generation = 0

            elif action == "step":
                self._step_conway()

            elif action == "start":
                if not self.running:
                    self.running = True
                    self._task = asyncio.create_task(
                        self._auto_step_loop()
                    )

            elif action == "stop":
                self.running = False

            elif action == "set_speed":
                self.speed = max(
                    0.02, float(data.get("speed", 0.1))
                )

        await self.broadcast()

    def _step_conway(self) -> None:
        """Simple inline Conway step for collaborative mode."""
        from scipy import signal
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        neighbors = signal.convolve2d(
            self.grid, kernel, mode="same", boundary="wrap",
        )
        self.grid = (
            ((self.grid == 1) & ((neighbors == 2) | (neighbors == 3)))
            | ((self.grid == 0) & (neighbors == 3))
        ).astype(int)
        self.generation += 1

    async def _auto_step_loop(self) -> None:
        """Run steps continuously until stopped."""
        while self.running:
            async with self._lock:
                self._step_conway()
            await self.broadcast()
            await asyncio.sleep(self.speed)


# Session registry
_collab_sessions: Dict[str, CollaborativeSession] = {}


def get_or_create_collab_session(
    session_id: str, width: int = 64, height: int = 64,
) -> CollaborativeSession:
    """Get an existing collaborative session or create a new one."""
    if session_id not in _collab_sessions:
        grid = np.zeros((height, width), dtype=int)
        _collab_sessions[session_id] = CollaborativeSession(grid=grid)
    return _collab_sessions[session_id]


async def collab_websocket_handler(
    websocket: WebSocket,
    session_id: str,
    width: int = 64,
    height: int = 64,
) -> None:
    """WebSocket endpoint handler for collaborative simulation."""
    session = get_or_create_collab_session(session_id, width, height)
    await session.add_client(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            await session.handle_message(websocket, data)
    except WebSocketDisconnect:
        session.remove_client(websocket)
    except (ConnectionError, RuntimeError):
        session.remove_client(websocket)
