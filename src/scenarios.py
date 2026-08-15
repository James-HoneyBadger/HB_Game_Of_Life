"""Reusable preset scenarios for LifeGrid.

The scenarios module provides a small catalog of common pattern seeds that can be
used to populate the grid immediately. Each scenario is represented as a list of
relative coordinates and is centered in the target grid automatically.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np

Pattern = List[Tuple[int, int]]
ScenarioTable = Dict[str, Pattern]


SCENARIOS: ScenarioTable = {
    "blinker": [(0, 0), (1, 0), (2, 0)],
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    "beacon": [(0, 0), (1, 0), (0, 1), (3, 2), (2, 3), (3, 3)],
    "toad": [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)],
    "lwss": [(1, 0), (4, 0), (0, 1), (0, 2), (4, 2), (0, 3), (1, 3), (2, 3), (3, 3)],
    "exploder": [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (2, 1),
        (0, 2), (2, 2),
        (0, 3), (1, 3), (2, 3),
    ],
    "acorn": [(1, 0), (3, 0), (0, 1), (1, 2), (2, 2), (3, 2)],
    "pulsar": [
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        (2, 12), (3, 12), (4, 12), (8, 12), (9, 12), (10, 12),
    ],
    "r-pentomino": [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    "diehard": [
        (0, 1), (1, 1), (1, 2), (6, 2), (7, 2), (8, 2),
        (2, 3), (3, 3), (4, 3),
    ],
    "pi-heptomino": [(1, 0), (2, 0), (0, 1), (2, 1), (1, 2), (2, 2), (1, 3)],
    "glider-gun": [
        (0, 4), (1, 4), (0, 5), (1, 5),
        (10, 4), (10, 5), (10, 6), (11, 3), (12, 2), (13, 2),
        (11, 7), (12, 8), (13, 8), (14, 5), (15, 3), (16, 4),
        (16, 5), (16, 6), (17, 5), (20, 2), (20, 3), (20, 4),
        (21, 2), (21, 3), (21, 4), (22, 1), (22, 5), (24, 0),
        (24, 1), (24, 5), (24, 6), (34, 2), (34, 3), (35, 2), (35, 3),
    ],
    "gosper-glider-gun": [
        (0, 4), (1, 4), (0, 5), (1, 5),
        (10, 4), (10, 5), (10, 6), (11, 3), (12, 2), (13, 2),
        (11, 7), (12, 8), (13, 8), (14, 5), (15, 3), (16, 4),
        (16, 5), (16, 6), (17, 5), (20, 2), (20, 3), (20, 4),
        (21, 2), (21, 3), (21, 4), (22, 1), (22, 5), (24, 0),
        (24, 1), (24, 5), (24, 6), (34, 2), (34, 3), (35, 2), (35, 3),
    ],
    "random": [],
}


def get_scenario_names() -> List[str]:
    """Return the available scenario names in a stable order."""
    return list(SCENARIOS.keys())


def _normalize_scenario_name(name: str) -> str:
    """Normalize a scenario name to its canonical key."""
    normalized = name.strip().lower().replace(" ", "-")
    if normalized in SCENARIOS:
        return normalized
    aliases = {
        "lightweight-spaceship": "lwss",
        "lightweight-spaceships": "lwss",
        "random-soup": "random",
        "gosper": "gosper-glider-gun",
        "gosper-glidergun": "gosper-glider-gun",
        "glidergun": "gosper-glider-gun",
        "glider-gun": "gosper-glider-gun",
        "glider-gun-ship": "gosper-glider-gun",
        "pi-heptomino": "pi-heptomino",
    }
    if normalized in aliases:
        return aliases[normalized]
    raise ValueError(f"Unknown scenario '{name}'. Available: {', '.join(get_scenario_names())}")


def _center_pattern(pattern: Iterable[Tuple[int, int]], width: int, height: int) -> Tuple[int, int]:
    """Compute the top-left placement for a pattern so it is centered."""
    coords = list(pattern)
    if not coords:
        return 0, 0
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    origin_x = (width - (max_x - min_x + 1)) // 2 - min_x
    origin_y = (height - (max_y - min_y + 1)) // 2 - min_y
    return origin_x, origin_y


def build_scenario(name: str, width: int, height: int) -> np.ndarray:
    """Construct a grid for a named scenario.

    Args:
        name: Scenario identifier such as "blinker" or "glider".
        width: Grid width in cells.
        height: Grid height in cells.

    Returns:
        A 2D numpy array populated according to the scenario.
    """
    if width <= 0 or height <= 0:
        raise ValueError("Scenario dimensions must be positive")

    key = _normalize_scenario_name(name)
    pattern = SCENARIOS[key]
    grid = np.zeros((height, width), dtype=int)

    if key == "random":
        rng = np.random.default_rng()
        grid = rng.integers(0, 2, size=(height, width), dtype=np.int8)
        return grid

    origin_x, origin_y = _center_pattern(pattern, width, height)
    for dx, dy in pattern:
        x = origin_x + dx
        y = origin_y + dy
        if 0 <= x < width and 0 <= y < height:
            grid[y, x] = 1

    return grid
