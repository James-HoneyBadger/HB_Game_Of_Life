"""Versioned simulation snapshot persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .boundary import BoundaryMode
from .config import SimulatorConfig
from .simulator import Simulator

SNAPSHOT_VERSION = 1


def _config_payload(config: SimulatorConfig) -> dict[str, Any]:
    payload = config.to_dict()
    payload["birth_rule"] = (
        sorted(config.birth_rule) if config.birth_rule is not None else None
    )
    payload["survival_rule"] = (
        sorted(config.survival_rule)
        if config.survival_rule is not None
        else None
    )
    return payload


def snapshot_dict(simulator: Simulator) -> dict[str, Any]:
    """Return a JSON-serializable snapshot of an initialized simulator."""
    if simulator.automaton is None:
        raise RuntimeError("Cannot snapshot an uninitialized simulator")
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "config": _config_payload(simulator.config),
        "generation": simulator.generation,
        "grid": simulator.automaton.grid.tolist(),
        "metrics": simulator.metrics_log,
        "rng_state": simulator.rng.bit_generator.state,
        "automaton_state": simulator.automaton.get_internal_state(),
    }


def save_snapshot(simulator: Simulator, filepath: str | Path) -> None:
    """Atomically write a simulator snapshot as formatted JSON."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snapshot_dict(simulator), indent=2)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def load_snapshot(filepath: str | Path) -> Simulator:
    """Load and validate a simulator snapshot."""
    path = Path(filepath)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return load_snapshot_dict(payload)


def load_snapshot_dict(payload: dict[str, Any]) -> Simulator:
    """Restore a simulator from an already decoded snapshot mapping."""
    if payload.get("snapshot_version") != SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {payload.get('snapshot_version')}"
        )

    config_payload = dict(payload.get("config", {}))
    if isinstance(config_payload.get("boundary_mode"), str):
        config_payload["boundary_mode"] = BoundaryMode.from_string(
            config_payload["boundary_mode"]
        )
    config = SimulatorConfig.from_dict(config_payload)

    simulator = Simulator(config)
    simulator.initialize(mode=config.automaton_mode, pattern="Empty")
    grid = np.asarray(payload["grid"], dtype=int)
    expected_shape = (config.height, config.width)
    if grid.shape != expected_shape:
        raise ValueError(
            f"Snapshot grid shape {grid.shape} does not match {expected_shape}"
        )
    state_count = simulator.automaton.get_state_count()
    if np.any(grid < 0) or np.any(grid >= state_count):
        raise ValueError(
            f"Snapshot contains states outside range 0..{state_count - 1}"
        )
    simulator.automaton.grid = grid.copy()
    simulator.automaton.restore_internal_state(
        payload.get("automaton_state", {})
    )
    simulator.generation = int(payload["generation"])
    simulator.metrics_log = list(payload.get("metrics", []))
    rng_state = payload.get("rng_state")
    if rng_state is not None:
        simulator.rng.bit_generator.state = rng_state
    simulator._reset_cycle_detection()
    return simulator
