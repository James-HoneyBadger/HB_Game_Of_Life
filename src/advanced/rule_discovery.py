"""
Rule discovery for identifying cellular automaton rules from patterns.

This module provides tools for analyzing grid patterns and discovering
the underlying rules that govern cell behavior.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

import numpy as np


@dataclass
class RulePattern:
    """A discovered rule pattern.

    Attributes:
        neighborhood: Tuple of neighbor states that trigger this rule
        current_state: Current state of the center cell
        next_state: Resulting state after rule application
        confidence: Confidence score (0-1) based on observations
        occurrences: Number of times this pattern was observed
    """

    neighborhood: Tuple[int, ...]
    current_state: int
    next_state: int
    confidence: float
    occurrences: int

    def __str__(self) -> str:
        """String representation."""
        neighbor_str = "".join(str(n) for n in self.neighborhood)
        return (
            f"Pattern: {neighbor_str} + state={self.current_state} "
            f"→ {self.next_state} "
            f"(confidence: {self.confidence:.2f}, n={self.occurrences})"
        )


class RuleDiscovery:
    """Discover cellular automaton rules from observations.

    This class analyzes grid transitions to identify the rules
    that govern cell behavior, useful for reverse-engineering
    unknown automata or validating implementations.

    Args:
        neighborhood_type: Type of neighborhood ('moore' or 'von_neumann')
    """

    def __init__(self, neighborhood_type: str = "moore"):
        if neighborhood_type not in ("moore", "von_neumann"):
            raise ValueError(
                f"Unknown neighborhood type: {neighborhood_type}. "
                "Use 'moore' or 'von_neumann'"
            )
        self.neighborhood_type = neighborhood_type
        self.observations: Dict[Tuple, List[int]] = {}

    def observe_transition(self, before: np.ndarray, after: np.ndarray) -> int:
        """Observe a grid transition and record patterns.

        Args:
            before: Grid state before transition
            after: Grid state after transition

        Returns:
            Number of patterns observed
        """
        if before.shape != after.shape:
            raise ValueError("Grid shapes must match")

        height, width = before.shape
        patterns_found = 0

        # Iterate through each cell
        for y in range(height):
            for x in range(width):
                # Get neighborhood
                neighbors = self._get_neighborhood(before, x, y)
                current_state = int(before[y, x])
                next_state = int(after[y, x])

                # Create pattern key
                pattern_key = (tuple(neighbors), current_state)

                # Record observation
                if pattern_key not in self.observations:
                    self.observations[pattern_key] = []
                self.observations[pattern_key].append(next_state)
                patterns_found += 1

        return patterns_found

    def _get_neighborhood(self, grid: np.ndarray, x: int, y: int) -> List[int]:
        """Get neighborhood of a cell.

        Args:
            grid: The grid
            x: X coordinate
            y: Y coordinate

        Returns:
            List of neighbor values
        """
        height, width = grid.shape
        neighbors = []

        if self.neighborhood_type == "moore":
            # Moore neighborhood (8 neighbors)
            offsets = [
                (-1, -1),
                (0, -1),
                (1, -1),
                (-1, 0),
                (1, 0),
                (-1, 1),
                (0, 1),
                (1, 1),
            ]
        else:
            # Von Neumann neighborhood (4 neighbors)
            offsets = [(0, -1), (-1, 0), (1, 0), (0, 1)]

        for dx, dy in offsets:
            nx, ny = x + dx, y + dy

            # Wrap around edges (toroidal)
            nx = nx % width
            ny = ny % height

            neighbors.append(int(grid[ny, nx]))

        return neighbors

    def get_discovered_rules(
        self, min_confidence: float = 0.8, min_occurrences: int = 5
    ) -> List[RulePattern]:
        """Get discovered rules that meet confidence thresholds.

        Args:
            min_confidence: Minimum confidence score (0-1)
            min_occurrences: Minimum number of observations

        Returns:
            List of RulePattern objects
        """
        rules = []

        for (
            (neighbors, current_state),
            next_states,
        ) in self.observations.items():
            if len(next_states) < min_occurrences:
                continue

            # Count occurrences of each next state
            state_counts = Counter(next_states)
            most_common_state, count = state_counts.most_common(1)[0]

            # Calculate confidence
            confidence = count / len(next_states)

            if confidence >= min_confidence:
                rule = RulePattern(
                    neighborhood=neighbors,
                    current_state=current_state,
                    next_state=most_common_state,
                    confidence=confidence,
                    occurrences=len(next_states),
                )
                rules.append(rule)

        # Sort by confidence and occurrences
        rules.sort(key=lambda r: (r.confidence, r.occurrences), reverse=True)

        return rules

    def infer_birth_survival_rules(
        self, min_confidence: float = 0.9
    ) -> Dict[str, Set[int]]:
        """Infer birth/survival rules (for Life-like automata).

        Args:
            min_confidence: Minimum confidence for rule inclusion

        Returns:
            Dictionary with 'birth' and 'survival' sets
        """
        rules = self.get_discovered_rules(min_confidence=min_confidence)

        birth_counts: Set[int] = set()
        survival_counts: Set[int] = set()

        for rule in rules:
            # Count alive neighbors
            alive_neighbors = sum(1 for n in rule.neighborhood if n != 0)

            # Birth: dead cell becomes alive
            if rule.current_state == 0 and rule.next_state != 0:
                birth_counts.add(alive_neighbors)

            # Survival: alive cell stays alive
            elif rule.current_state != 0 and rule.next_state != 0:
                survival_counts.add(alive_neighbors)

        return {"birth": birth_counts, "survival": survival_counts}

    def format_birth_survival_notation(
        self, birth: Set[int], survival: Set[int]
    ) -> str:
        """Format rules in B/S notation (e.g., B3/S23 for Conway's Life).

        Args:
            birth: Set of neighbor counts that cause birth
            survival: Set of neighbor counts that allow survival

        Returns:
            Rule string in B/S notation
        """
        birth_str = "".join(str(n) for n in sorted(birth))
        survival_str = "".join(str(n) for n in sorted(survival))
        return f"B{birth_str}/S{survival_str}"

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get a summary of discovered rules.

        Returns:
            Dictionary with rule statistics
        """
        total_observations = sum(
            len(states) for states in self.observations.values()
        )
        unique_patterns = len(self.observations)

        # Get confident rules
        high_confidence_rules = self.get_discovered_rules(min_confidence=0.9)
        medium_confidence_rules = self.get_discovered_rules(min_confidence=0.7)

        return {
            "total_observations": total_observations,
            "unique_patterns": unique_patterns,
            "high_confidence_rules": len(high_confidence_rules),
            "medium_confidence_rules": len(medium_confidence_rules),
            "neighborhood_type": self.neighborhood_type,
        }

    def reset(self) -> None:
        """Clear all observations."""
        self.observations.clear()

    def export_rules(self, filepath: str) -> None:
        """Export discovered rules to a file.

        Args:
            filepath: Path to output file
        """
        rules = self.get_discovered_rules(min_confidence=0.7)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Cellular Automaton Rules Discovery\n")
            f.write(f"Neighborhood Type: {self.neighborhood_type}\n")
            f.write(f"Total Unique Patterns: {len(self.observations)}\n")
            f.write(f"High Confidence Rules: {len(rules)}\n")
            f.write("\n" + "=" * 70 + "\n\n")

            # Try to infer B/S notation
            try:
                bs_rules = self.infer_birth_survival_rules(min_confidence=0.9)
                bs_notation = self.format_birth_survival_notation(
                    bs_rules["birth"], bs_rules["survival"]
                )
                f.write(f"Inferred B/S Notation: {bs_notation}\n")
                f.write(f"Birth: {sorted(bs_rules['birth'])}\n")
                f.write(f"Survival: {sorted(bs_rules['survival'])}\n")
                f.write("\n" + "=" * 70 + "\n\n")
            except Exception as e:  # pylint: disable=broad-exception-caught
                f.write(f"Could not infer B/S Notation: {e}\n")
                f.write("\n" + "=" * 70 + "\n\n")

            # Write detailed rules
            f.write("Detailed Rules:\n\n")
            for i, rule in enumerate(rules[:100], 1):  # Limit to top 100
                f.write(f"{i}. {rule}\n")
