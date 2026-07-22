"""Cellular Automaton implementations"""

from .ant import LangtonsAnt
from .base import CellularAutomaton
from .briansbrain import BriansBrain
from .conway import ConwayGameOfLife
from .generations import GenerationsAutomaton
from .hexagonal import HexagonalGameOfLife
from .highlife import HighLife
from .immigration import ImmigrationGame
from .lifelike import LifeLikeAutomaton, parse_bs
from .rainbow import RainbowGame
from .wireworld import Wireworld

__all__ = [
    "CellularAutomaton",
    "ConwayGameOfLife",
    "HexagonalGameOfLife",
    "HighLife",
    "ImmigrationGame",
    "RainbowGame",
    "LangtonsAnt",
    "LifeLikeAutomaton",
    "parse_bs",
    "Wireworld",
    "BriansBrain",
    "GenerationsAutomaton",
]
