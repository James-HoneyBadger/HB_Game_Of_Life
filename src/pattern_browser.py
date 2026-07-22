"""Pattern browser and preset management."""

from __future__ import annotations

from typing import Dict, List, Optional

from patterns import PATTERN_DATA


class PatternBrowser:
    """Browse and manage pattern presets.

    Provides a searchable interface to built-in patterns with descriptions.
    """

    def __init__(self) -> None:
        """Initialize pattern browser."""
        # Using Any to avoid deep type matching issues across modules
        # without shared alias
        self.patterns = PATTERN_DATA  # type: ignore

    def get_modes(self) -> list[str]:
        """Get available automaton modes.

        Returns:
            List of mode names
        """
        return list(self.patterns.keys())

    def get_patterns(self, mode: str) -> list[str]:
        """Get patterns for a mode.

        Args:
            mode: Automaton mode name

        Returns:
            List of pattern names
        """
        return list(self.patterns.get(mode, {}).keys())

    def get_pattern_description(self, mode: str, pattern: str) -> str:
        """Get description of a pattern.

        Args:
            mode: Automaton mode name
            pattern: Pattern name

        Returns:
            Description string
        """
        mode_patterns = self.patterns.get(mode, {})
        if pattern in mode_patterns:
            _, description = mode_patterns[pattern]
            return description
        return ""

    def get_pattern_coordinates(self, mode: str, pattern: str) -> List[tuple]:
        """Get coordinate data for a pattern.

        Args:
            mode: Automaton mode name
            pattern: Pattern name

        Returns:
            List of (x, y) coordinate tuples
        """
        mode_patterns = self.patterns.get(mode, {})
        if pattern in mode_patterns:
            coords, _ = mode_patterns[pattern]
            return coords
        return []

    def search_patterns(self, query: str) -> Dict[str, List[str]]:
        """Search patterns by name.

        Args:
            query: Search query string (case-insensitive)

        Returns:
            Dict mapping modes to matching pattern names
        """
        query_lower = query.lower()
        results: Dict[str, List[str]] = {}

        for mode, patterns in self.patterns.items():
            matching = [
                name for name in patterns if query_lower in name.lower()
            ]
            if matching:
                results[mode] = matching

        return results

    def get_patterns_by_description(self, query: str) -> Dict[str, List[str]]:
        """Search patterns by description.

        Args:
            query: Search query string (case-insensitive)

        Returns:
            Dict mapping modes to matching pattern names
        """
        query_lower = query.lower()
        results: Dict[str, List[str]] = {}

        for mode, patterns in self.patterns.items():
            matching = []
            for name, (_, desc) in patterns.items():
                if query_lower in desc.lower():
                    matching.append(name)

            if matching:
                results[mode] = matching

        return results

    def get_pattern_info(self, mode: str, pattern: str) -> Optional[dict]:
        """Get complete information about a pattern.

        Args:
            mode: Automaton mode name
            pattern: Pattern name

        Returns:
            Dict with pattern info or None if not found
        """
        mode_patterns = self.patterns.get(mode, {})
        if pattern in mode_patterns:
            coords, description = mode_patterns[pattern]
            return {
                "name": pattern,
                "mode": mode,
                "description": description,
                "cell_count": len(coords),
                "coordinates": coords,
            }
        return None

    def get_most_popular_patterns(
        self, mode: str, limit: int = 5
    ) -> list[str]:
        """Get most popular patterns for a mode.

        Returns the first N patterns (typically most popular).

        Args:
            mode: Automaton mode name
            limit: Maximum number to return

        Returns:
            List of pattern names
        """
        patterns = list(self.patterns.get(mode, {}).keys())
        return patterns[:limit]

    def get_statistics(self) -> dict:
        """Get statistics about available patterns.

        Returns:
            Dict with statistics
        """
        total_patterns = 0
        patterns_per_mode = {}

        for mode, patterns in self.patterns.items():
            count = len(patterns)
            patterns_per_mode[mode] = count
            total_patterns += count

        return {
            "total_modes": len(self.patterns),
            "total_patterns": total_patterns,
            "patterns_per_mode": patterns_per_mode,
        }
