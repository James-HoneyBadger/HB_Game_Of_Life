"""Pattern favorites and history management.

This module provides functionality for managing favorite patterns,
recent pattern history, and pattern similarity search.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np


@dataclass
class PatternEntry:
    """A pattern entry in favorites or history.

    Attributes:
        name: Pattern name
        mode: Automaton mode (e.g., 'conway')
        grid_data: Serialized grid data (list of [x, y] coordinates)
        width: Grid width
        height: Grid height
        timestamp: When the pattern was added/used
        tags: Optional tags for categorization
        description: Optional description
        favorite: Whether this is marked as favorite
    """

    name: str
    mode: str
    grid_data: List[List[int]]
    width: int
    height: int
    timestamp: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    favorite: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PatternEntry:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_grid(
        cls,
        name: str,
        mode: str,
        grid: np.ndarray,
        tags: Optional[List[str]] = None,
        description: str = "",
        favorite: bool = False,
    ) -> PatternEntry:
        """Create pattern entry from a grid.

        Args:
            name: Pattern name
            mode: Automaton mode
            grid: 2D numpy array
            tags: Optional tags
            description: Optional description
            favorite: Whether to mark as favorite

        Returns:
            PatternEntry instance
        """
        height, width = grid.shape

        # Extract live cell coordinates
        coords = np.argwhere(grid > 0).tolist()
        # Convert from [y, x] to [x, y]
        grid_data = [[int(x), int(y)] for y, x in coords]

        timestamp = datetime.now().isoformat()

        return cls(
            name=name,
            mode=mode,
            grid_data=grid_data,
            width=width,
            height=height,
            timestamp=timestamp,
            tags=tags or [],
            description=description,
            favorite=favorite,
        )

    def to_grid(self) -> np.ndarray:
        """Convert to numpy grid.

        Returns:
            2D numpy array representing the pattern
        """
        grid = np.zeros((self.height, self.width), dtype=int)
        for x, y in self.grid_data:
            if 0 <= y < self.height and 0 <= x < self.width:
                grid[y, x] = 1
        return grid


class PatternManager:
    """Manages pattern favorites and history.

    Args:
        data_dir: Directory to store pattern data
        max_history: Maximum number of history entries to keep
    """

    def __init__(
        self, data_dir: str = "user_data", max_history: int = 50
    ) -> None:
        """Initialize pattern manager."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.favorites_file = self.data_dir / "favorites.json"
        self.history_file = self.data_dir / "history.json"

        self.max_history = max_history

        self.favorites: List[PatternEntry] = []
        self.history: List[PatternEntry] = []

        self._load()

    def _load(self) -> None:
        """Load favorites and history from disk."""
        # Load favorites
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorites = [
                        PatternEntry.from_dict(item) for item in data
                    ]
            except (json.JSONDecodeError, KeyError, TypeError):
                self.favorites = []

        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = [
                        PatternEntry.from_dict(item) for item in data
                    ]
            except (json.JSONDecodeError, KeyError, TypeError):
                self.history = []

    def _save(self) -> None:
        """Save favorites and history to disk."""
        # Save favorites
        with open(self.favorites_file, "w", encoding="utf-8") as f:
            json.dump(
                [entry.to_dict() for entry in self.favorites],
                f,
                indent=2,
            )

        # Save history
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(
                [entry.to_dict() for entry in self.history],
                f,
                indent=2,
            )

    def add_favorite(self, entry: PatternEntry) -> None:
        """Add a pattern to favorites.

        Args:
            entry: Pattern entry to add
        """
        entry.favorite = True
        # Remove if already exists (by name)
        self.favorites = [f for f in self.favorites if f.name != entry.name]
        self.favorites.append(entry)
        self._save()

    def remove_favorite(self, name: str) -> bool:
        """Remove a pattern from favorites.

        Args:
            name: Pattern name to remove

        Returns:
            True if pattern was found and removed
        """
        original_len = len(self.favorites)
        self.favorites = [f for f in self.favorites if f.name != name]

        if len(self.favorites) < original_len:
            self._save()
            return True
        return False

    def get_favorites(self) -> List[PatternEntry]:
        """Get all favorite patterns.

        Returns:
            List of favorite patterns, sorted by timestamp (newest first)
        """
        return sorted(
            self.favorites,
            key=lambda x: x.timestamp,
            reverse=True,
        )

    def is_favorite(self, name: str) -> bool:
        """Check if a pattern is in favorites.

        Args:
            name: Pattern name

        Returns:
            True if pattern is favorited
        """
        return any(f.name == name for f in self.favorites)

    def add_to_history(self, entry: PatternEntry) -> None:
        """Add a pattern to history.

        Args:
            entry: Pattern entry to add
        """
        # Remove duplicates (same name and mode)
        self.history = [
            h
            for h in self.history
            if not (h.name == entry.name and h.mode == entry.mode)
        ]

        # Add to front
        self.history.insert(0, entry)

        # Limit size
        if len(self.history) > self.max_history:
            self.history = self.history[: self.max_history]

        self._save()

    def get_history(self, limit: Optional[int] = None) -> List[PatternEntry]:
        """Get recent pattern history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent patterns
        """
        if limit:
            return self.history[:limit]
        return self.history

    def clear_history(self) -> None:
        """Clear all history."""
        self.history.clear()
        self._save()

    def search_by_tag(self, tag: str) -> List[PatternEntry]:
        """Search patterns by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching patterns
        """
        results = []

        for entry in self.favorites + self.history:
            if tag.lower() in [t.lower() for t in entry.tags]:
                results.append(entry)

        # Remove duplicates
        seen = set()
        unique_results = []
        for entry in results:
            key = (entry.name, entry.mode)
            if key not in seen:
                seen.add(key)
                unique_results.append(entry)

        return unique_results

    def search_by_name(self, query: str) -> List[PatternEntry]:
        """Search patterns by name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching patterns
        """
        query_lower = query.lower()
        results = []

        for entry in self.favorites + self.history:
            if query_lower in entry.name.lower():
                results.append(entry)

        # Remove duplicates
        seen = set()
        unique_results = []
        for entry in results:
            key = (entry.name, entry.mode)
            if key not in seen:
                seen.add(key)
                unique_results.append(entry)

        return unique_results

    def find_similar(
        self, reference: PatternEntry, threshold: float = 0.8
    ) -> List[tuple[PatternEntry, float]]:
        """Find patterns similar to a reference pattern.

        Uses Jaccard similarity on cell positions.

        Args:
            reference: Reference pattern
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (pattern, similarity_score) tuples
        """
        ref_set = set(tuple(coord) for coord in reference.grid_data)
        results = []

        for entry in self.favorites + self.history:
            # Skip same pattern
            if entry.name == reference.name and entry.mode == reference.mode:
                continue

            entry_set = set(tuple(coord) for coord in entry.grid_data)

            # Calculate Jaccard similarity
            if len(ref_set) == 0 and len(entry_set) == 0:
                similarity = 1.0
            elif len(ref_set) == 0 or len(entry_set) == 0:
                similarity = 0.0
            else:
                intersection = len(ref_set & entry_set)
                union = len(ref_set | entry_set)
                similarity = intersection / union if union > 0 else 0.0

            if similarity >= threshold:
                results.append((entry, similarity))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results
