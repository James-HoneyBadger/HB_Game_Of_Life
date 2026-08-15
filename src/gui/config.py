"""Static configuration shared by the GUI components."""

from __future__ import annotations

from typing import Dict, List

from automata import parse_bs
from core.registry import iter_modes
from scenarios import get_scenario_names

# pylint: disable=import-error


# Default custom rule (Conway)
DEFAULT_CUSTOM_RULE = "B3/S23"
DEFAULT_CUSTOM_BIRTH, DEFAULT_CUSTOM_SURVIVAL = parse_bs(DEFAULT_CUSTOM_RULE)

# Factory registry for standard modes
MODE_FACTORIES = {
    descriptor.name: descriptor.factory
    for descriptor in iter_modes()
    if descriptor.factory is not None
}

# Pattern options per mode
MODE_PATTERNS: Dict[str, List[str]] = {
    "Conway's Game of Life": [
        "Glider",
        "Blinker",
        "Toad",
        "Beacon",
        "Block",
        "Beehive",
        "Loaf",
        "Boat",
        "LWSS",
        "MWSS",
        "Glider Gun",
        "Acorn",
        "R-Pentomino",
        "Pulsar",
        "Lightweight Spaceship",
        *get_scenario_names(),
        "Random Soup",
    ],
    "HighLife": ["Replicator", "Random Soup"],
    "Hexagonal Life": ["Random Soup"],
    "Immigration": ["Color Mix", "Random Soup"],
    "Rainbow": ["Rainbow Mix", "Random Soup"],
    "Langton's Ant": ["Empty"],
    "Wireworld": ["Random Soup"],
    "Brian's Brain": ["Random Soup"],
    "Generations": ["Random Soup"],
    "Custom Rules": ["Random Soup"],
}

# Color map shared by export and canvas painting
CELL_COLORS = {
    0: "white",
    1: "black",
    2: "red",
    3: "orange",
    4: "yellow",
    5: "green",
    6: "blue",
    7: "purple",
    8: "#444444",
    9: "#888888",
}

EXPORT_COLOR_MAP = {
    0: (255, 255, 255),
    1: (0, 0, 0),
    2: (255, 0, 0),
    3: (255, 128, 0),
    4: (255, 255, 0),
    5: (0, 200, 0),
    6: (0, 0, 255),
    7: (150, 0, 255),
    8: (68, 68, 68),
    9: (136, 136, 136),
}

MAX_HISTORY_LENGTH = 500
MIN_GRID_SIZE = 10
MAX_GRID_SIZE = 500
DEFAULT_CELL_SIZE = 8
MIN_CELL_SIZE = 2
MAX_CELL_SIZE = 32
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 600
DEFAULT_SPEED = 50
