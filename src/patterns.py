"""Pattern definitions and loading utilities for cellular automata."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Tuple

import numpy as np

PatternInfo = Tuple[List[Tuple[int, int]], str]
CategoryData = Dict[str, PatternInfo]
AllPatterns = Dict[str, CategoryData]


def load_pattern_data() -> AllPatterns:
    """Load pattern data from JSON file."""
    try:
        json_path = os.path.join(
            os.path.dirname(__file__),
            "data",
            "patterns.json",
        )
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert list of lists to list of tuples for compatibility
        processed_data: AllPatterns = {}
        for category, patterns in data.items():
            processed_data[category] = {}
            for name, details in patterns.items():
                points = [tuple(p) for p in details["points"]]
                processed_data[category][name] = (
                    points,
                    details["description"],
                )
        return processed_data
    except (IOError, ValueError, json.JSONDecodeError) as e:
        logging.error("Failed to load patterns.json: %s", e)
        return {}


# Base pattern data structure
BASE_PATTERNS: AllPatterns = {
    "High Life": {
        "Replicator": (
            [(1, 0), (0, 1), (1, 1), (2, 1), (0, 2), (2, 2), (1, 3)],
            "Replicator - grows exponentially",
        ),
        "Random Soup": (
            [],
            "Random 15% fill to explore emergent structures",
        ),
    },
    "Immigration Game": {
        "Color Mix": ([], "Seeds multiple colors for domain competition"),
        "Random Soup": ([], "Random 15% fill with two-state colors"),
    },
    "Rainbow Game": {
        "Rainbow Mix": ([], "Multi-color seed mix for rainbow rule"),
        "Random Soup": ([], "Random 15% fill across rainbow states"),
    },
    "Langton's Ant": {
        "Empty": ([], "Blank grid to let the ant roam"),
    },
    "Wireworld": {
        "Random Soup": ([], "Random conductors for Wireworld experiments"),
    },
    "Brian's Brain": {
        "Random Soup": ([], "Random firing/ready cells"),
    },
    "Generations": {
        "Random Soup": ([], "Randomized seeds for multi-state fading"),
    },
    "Custom Rules": {
        "Random Soup": ([], "Random fill using the active custom rule"),
    },
}

# Merge JSON data with base patterns
JSON_PATTERNS = load_pattern_data()
PATTERN_DATA: AllPatterns = {**BASE_PATTERNS}
if "Conway's Game of Life" in JSON_PATTERNS:
    PATTERN_DATA["Conway's Game of Life"] = JSON_PATTERNS["Conway's Game of Life"]
else:
    # Fallback if load failed
    PATTERN_DATA["Conway's Game of Life"] = {}

# Add Random Soup to Conway manually since it's procedural
PATTERN_DATA["Conway's Game of Life"]["Random Soup"] = (
    [],
    "Random 15% fill to explore emergent structures",
)


def get_pattern_coords(mode: str, pattern_name: str) -> List[Tuple[int, int]]:
    """Get the coordinates for a named pattern."""
    if mode in PATTERN_DATA and pattern_name in PATTERN_DATA[mode]:
        return PATTERN_DATA[mode][pattern_name][0]
    return []


def get_pattern_description(mode: str, pattern_name: str) -> str:
    """Get the description for a named pattern."""
    if mode in PATTERN_DATA and pattern_name in PATTERN_DATA[mode]:
        return PATTERN_DATA[mode][pattern_name][1]
    return ""


def apply_pattern_to_grid(
    grid: np.ndarray,
    pattern_coords: List[Tuple[int, int]],
    center_x: int,
    center_y: int,
) -> None:
    """Apply a pattern to the grid centered at the given coordinates."""
    height, width = grid.shape
    for dx, dy in pattern_coords:
        x = center_x + dx
        y = center_y + dy
        if 0 <= x < width and 0 <= y < height:
            grid[y, x] = 1
