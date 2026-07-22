"""Day and Night rule plugin."""

from automata import LifeLikeAutomaton
from plugin_system import AutomatonPlugin


class DayAndNightPlugin(AutomatonPlugin):
    """Plugin for the Day & Night cellular automaton rule."""

    @property
    def name(self) -> str:
        return "Day & Night"

    @property
    def description(self) -> str:
        return (
            "B3678/S34678 - A rule with symmetric behavior for ON/OFF cells."
        )

    @property
    def version(self) -> str:
        return "1.0"

    def create_automaton(self, width: int, height: int):
        return LifeLikeAutomaton(
            width, height,
            birth={3, 6, 7, 8},
            survival={3, 4, 6, 7, 8}
        )
