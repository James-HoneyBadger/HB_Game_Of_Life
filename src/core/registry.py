"""Canonical automaton mode registry shared by all frontends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator

from automata import (
    BriansBrain,
    CellularAutomaton,
    ConwayGameOfLife,
    GenerationsAutomaton,
    HexagonalGameOfLife,
    HighLife,
    ImmigrationGame,
    LangtonsAnt,
    RainbowGame,
    Wireworld,
)

AutomatonFactory = Callable[[int, int], CellularAutomaton]


@dataclass(frozen=True)
class ModeDescriptor:
    """Metadata and factory information for one simulation mode."""

    name: str
    description: str
    factory: AutomatonFactory | None
    aliases: tuple[str, ...] = ()
    state_count: int | None = 2
    supports_patterns: bool = True
    source: str = "builtin"
    api_version: int = 1
    capabilities: dict[str, bool] = field(default_factory=dict)


_DESCRIPTORS: list[ModeDescriptor] = [
    ModeDescriptor("Conway's Game of Life", "Classic B3/S23 cellular automaton", ConwayGameOfLife, ("conway",)),
    ModeDescriptor("HighLife", "B36/S23 replicator rule", HighLife, ("highlife",)),
    ModeDescriptor("Immigration", "Two-color Conway variant", ImmigrationGame, ("immigration",), 4),
    ModeDescriptor("Rainbow", "Multi-state color variant", RainbowGame, ("rainbow",), 7),
    ModeDescriptor("Wireworld", "Four-state electronic circuit simulation", Wireworld, ("wireworld",), 4),
    ModeDescriptor("Brian's Brain", "Three-state firing and refractory automaton", BriansBrain, ("briansbrain", "brians brain"), 3),
    ModeDescriptor("Langton's Ant", "Ant-based grid automaton", LangtonsAnt, ("ant",), None),
    ModeDescriptor("Generations", "Multi-state fading automaton", GenerationsAutomaton, ("generations",), None),
    ModeDescriptor("Hexagonal Life", "Six-neighbor B2/S34 hexagonal layout", HexagonalGameOfLife, ("hexagonal",)),
    ModeDescriptor("Custom Rules", "User-provided B/S rule sets", None),
]

_BY_NAME = {descriptor.name: descriptor for descriptor in _DESCRIPTORS}
_BY_ALIAS = {
    alias: descriptor
    for descriptor in _DESCRIPTORS
    for alias in descriptor.aliases
}


def normalize_mode(name: str) -> str:
    """Return a canonical mode name for a name or alias."""
    normalized = name.lower().replace("_", " ").replace("-", " ").strip()
    for descriptor in _DESCRIPTORS:
        if descriptor.name.lower() == normalized:
            return descriptor.name
    descriptor = _BY_ALIAS.get(normalized)
    if descriptor is None:
        raise ValueError(f"Unknown automaton mode: {name}")
    return descriptor.name


def get_mode(name: str) -> ModeDescriptor:
    """Return the descriptor for a canonical name or alias."""
    return _BY_NAME[normalize_mode(name)]


def iter_modes() -> Iterator[ModeDescriptor]:
    """Iterate over descriptors in stable display order."""
    return iter(_DESCRIPTORS)


def register_mode(descriptor: ModeDescriptor) -> None:
    """Register or replace a runtime mode descriptor."""
    global _BY_NAME, _BY_ALIAS
    for alias in descriptor.aliases:
        existing = _BY_ALIAS.get(alias)
        if existing is not None and existing.name != descriptor.name:
            raise ValueError(
                f"Mode alias '{alias}' is already registered by "
                f"{existing.name}"
            )
    _DESCRIPTORS[:] = [
        existing for existing in _DESCRIPTORS
        if existing.name != descriptor.name
    ]
    _DESCRIPTORS.append(descriptor)
    _BY_NAME = {item.name: item for item in _DESCRIPTORS}
    _BY_ALIAS = {
        alias: item
        for item in _DESCRIPTORS
        for alias in item.aliases
    }
