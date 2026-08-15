"""Regression tests for the headless simulation surface."""

import json
import csv
from io import StringIO
import numpy as np
import pytest

from advanced.rle_format import RLEEncoder, RLEParser
from api.app import CreateSessionRequest, StepRequest, create_session
from automata import HexagonalGameOfLife, LifeLikeAutomaton, compare_bs_rules
from cli import main
from core.config import SimulatorConfig
from core.boundary import BoundaryMode, convolve_with_boundary
from core.registry import get_mode, iter_modes, normalize_mode
from core.metrics import calculate_transition_metrics
from core.snapshot import load_snapshot, load_snapshot_dict, save_snapshot, snapshot_dict
from core.simulator import Simulator
from export_manager import ExportManager
from autosave_manager import AutoSaveManager
from patterns import PATTERN_DATA
from plugin_system import PluginManager
from scenarios import build_scenario, get_scenario_names
from gui.new_features import BookmarkManager


def test_conway_pattern_data_is_available() -> None:
    assert "Glider" in PATTERN_DATA["Conway's Game of Life"]


def test_scenario_aliases_and_extended_catalog_are_available() -> None:
    names = get_scenario_names()
    assert "diehard" in names
    assert "pi-heptomino" in names
    assert "gosper-glider-gun" in names
    assert "lwss" in names
    assert build_scenario("gosper-glider-gun", 30, 30).shape == (30, 30)
    assert build_scenario("lightweight-spaceship", 12, 12).sum() > 0
    assert build_scenario("glider-gun", 30, 30).sum() > 0


def test_scenario_presets_are_available_and_apply_to_grid() -> None:
    names = get_scenario_names()
    assert "blinker" in names
    assert "acorn" in names
    assert "glider-gun" in names
    grid = build_scenario("blinker", 9, 9)
    assert grid.shape == (9, 9)
    assert int(grid.sum()) == 3


def test_conway_scenario_presets_and_bookmarks_are_available() -> None:
    names = get_scenario_names()
    assert "blinker" in names
    assert "acorn" in names

    manager = BookmarkManager()
    manager.add("interesting", 12)
    manager.add("later", 18)
    assert manager.get(12) == "interesting"
    assert manager.snapshot(12) == {"interesting": 12}
    assert manager.list_bookmarks() == {"interesting": 12, "later": 18}
    manager.remove("interesting")
    assert manager.snapshot() == {"later": 18}


def test_cli_accepts_named_scenario_presets(tmp_path) -> None:
    output = tmp_path / "scenario.json"
    assert main([
        "--scenario", "blinker",
        "--width", "9",
        "--height", "9",
        "--steps", "1",
        "--quiet",
        "--export", str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["final_population"] == 3


def test_custom_rule_and_hexagonal_modes_initialize() -> None:
    custom = Simulator(
        SimulatorConfig(
            width=12,
            height=12,
            automaton_mode="Custom Rules",
            birth_rule={3, 6},
            survival_rule={2, 3},
        )
    )
    custom.initialize()
    assert isinstance(custom.automaton, LifeLikeAutomaton)
    assert custom.step()

    hexagonal = Simulator(
        SimulatorConfig(width=12, height=12, automaton_mode="Hexagonal Life")
    )
    hexagonal.initialize(pattern="Random Soup")
    assert isinstance(hexagonal.automaton, HexagonalGameOfLife)
    assert hexagonal.step()


def test_all_registered_automata_share_pattern_and_cell_contract() -> None:
    from core.registry import iter_modes

    for descriptor in iter_modes():
        if descriptor.factory is None:
            continue
        automaton = descriptor.factory(8, 8)
        automaton.load_pattern("Empty")
        automaton.set_cell(2, 3, 1)
        assert automaton.get_grid().shape == (8, 8)
        assert automaton.get_state_count() >= 2


def test_builtin_automata_reject_unknown_patterns() -> None:
    from core.registry import iter_modes

    for descriptor in iter_modes():
        if descriptor.factory is None:
            continue
        automaton = descriptor.factory(8, 8)
        try:
            automaton.load_pattern("not-a-real-pattern")
        except ValueError as exc:
            assert "Unsupported pattern" in str(exc)
        else:
            raise AssertionError(f"{descriptor.name} accepted an unknown pattern")


def test_multistate_automata_report_complete_state_counts() -> None:
    from automata import BriansBrain, GenerationsAutomaton, ImmigrationGame
    from automata import RainbowGame, Wireworld

    assert BriansBrain(4, 4).get_state_count() == 3
    assert ImmigrationGame(4, 4).get_state_count() == 4
    assert RainbowGame(4, 4).get_state_count() == 7
    assert Wireworld(4, 4).get_state_count() == 4
    assert GenerationsAutomaton(4, 4, n_states=9).get_state_count() == 9


def test_wraparound_aliases_enable_cross_boundary_motion() -> None:
    assert BoundaryMode.from_string("wrap") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("toroidal") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("wrap-around") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("wrap around") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("continuous") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("periodic") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("periodic boundary") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("circular") is BoundaryMode.WRAP
    assert BoundaryMode.from_string("fixed") is BoundaryMode.FIXED
    assert BoundaryMode.from_string("fill") is BoundaryMode.FIXED
    assert BoundaryMode.from_string("dead") is BoundaryMode.FIXED
    assert BoundaryMode.from_string("reflect") is BoundaryMode.REFLECT
    assert BoundaryMode.from_string("symm") is BoundaryMode.REFLECT
    assert BoundaryMode.from_string("mirror") is BoundaryMode.REFLECT
    assert BoundaryMode.from_string("mirror mode") is BoundaryMode.REFLECT

    wrapped = Simulator(
        SimulatorConfig(width=3, height=3, boundary_mode=BoundaryMode.WRAP)
    )
    wrapped.initialize(pattern="Empty")
    wrapped.set_cell(0, 0)
    wrapped.set_cell(0, 1)
    wrapped.set_cell(1, 0)
    wrapped.step()
    assert wrapped.get_grid()[2, 2] == 1


def test_rule_comparison_reports_birth_and_survival_differences() -> None:
    comparison = compare_bs_rules("B3/S23", "B36/S23")
    assert comparison["shared_birth"] == {3}
    assert comparison["exclusive_birth_a"] == set()
    assert comparison["exclusive_birth_b"] == {6}
    assert comparison["shared_survival"] == {2, 3}
    assert comparison["exclusive_survival_a"] == set()
    assert comparison["exclusive_survival_b"] == set()


def test_wrap_boundary_keeps_gliders_continuing_across_edges() -> None:
    sim = Simulator(SimulatorConfig(width=8, height=8, boundary_mode=BoundaryMode.WRAP))
    sim.initialize(pattern="Empty")
    for x, y in [(7, 0), (7, 1), (7, 2), (6, 2), (5, 1)]:
        sim.set_cell(x, y, 1)

    for _ in range(8):
        sim.step()

    assert sim.get_grid()[:, 0].any()
    assert sim.get_grid()[:, 7].any()


def test_conway_boundary_mode_changes_edge_neighbors() -> None:
    fixed = Simulator(
        SimulatorConfig(width=3, height=3, boundary_mode=BoundaryMode.FIXED)
    )
    fixed.initialize(pattern="Empty")
    fixed.set_cell(0, 0)
    fixed.set_cell(0, 1)
    fixed.set_cell(1, 0)
    fixed.step()

    wrapped = Simulator(
        SimulatorConfig(width=3, height=3, boundary_mode=BoundaryMode.WRAP)
    )
    wrapped.initialize(pattern="Empty")
    wrapped.set_cell(0, 0)
    wrapped.set_cell(0, 1)
    wrapped.set_cell(1, 0)
    wrapped.step()

    assert fixed.get_grid()[2, 2] == 0
    assert wrapped.get_grid()[2, 2] == 1


def test_all_builtin_modes_step_with_each_boundary_mode() -> None:
    from core.registry import iter_modes

    for boundary in BoundaryMode:
        for descriptor in iter_modes():
            if descriptor.factory is None:
                continue
            automaton = descriptor.factory(8, 8)
            automaton.set_boundary_mode(boundary)
            automaton.load_pattern("Random Soup")
            automaton.step()
            assert automaton.get_grid().shape == (8, 8)


def test_canonical_mode_registry_resolves_aliases() -> None:
    assert normalize_mode("conway") == "Conway's Game of Life"
    assert normalize_mode("HEXAGONAL") == "Hexagonal Life"
    assert get_mode("brians-brain").state_count == 3
    assert {mode.name for mode in iter_modes()} >= {
        "Conway's Game of Life", "Custom Rules", "Hexagonal Life",
    }


def test_cli_custom_rule_and_hexagonal_modes() -> None:
    assert main(["--rule", "B36/S23", "--steps", "1", "--quiet"]) == 0
    assert main(["--mode", "hexagonal", "--steps", "1", "--quiet"]) == 0


def test_cli_loads_plugin_modes() -> None:
    assert main(["--mode", "Day & Night", "--steps", "1", "--quiet"]) == 0


def test_cli_lists_modes_and_patterns(capsys) -> None:
    assert main(["--list-modes"]) == 0
    assert "Conway's Game of Life" in capsys.readouterr().out
    assert main(["--list-patterns", "--mode", "conway"]) == 0
    out = capsys.readouterr().out
    assert "Glider" in out
    assert "blinker" in out


def test_cli_lists_boundary_modes(capsys) -> None:
    assert main(["--list-boundaries"]) == 0
    out = capsys.readouterr().out
    assert "wrap" in out
    assert "toroidal" in out
    assert "continuous" in out


def test_cli_boundary_help_lists_aliases() -> None:
    from cli import _build_parser

    help_text = _build_parser().format_help()
    assert "wrap-around" in help_text
    assert "reflect" in help_text
    assert "mirror" in help_text


def test_cli_pattern_listing_rejects_unknown_mode() -> None:
    assert main(["--list-patterns", "--mode", "not-a-mode"]) == 1


def test_cli_boundary_is_recorded_in_json_export(tmp_path) -> None:
    output = tmp_path / "fixed.json"
    assert main([
        "--steps", "0", "--boundary", "fixed", "--quiet",
        "--export", str(output),
    ]) == 0
    assert '"boundary": "fixed"' in output.read_text(encoding="utf-8")


def test_app_config_persists_boundary_mode() -> None:
    from config_manager import AppConfig

    config = AppConfig.from_dict({"boundary_mode": "reflect"})
    assert config.boundary_mode == "reflect"


def test_simulator_config_round_trips_seed_and_boundary() -> None:
    config = SimulatorConfig(seed=17, boundary_mode=BoundaryMode.FIXED)
    restored = SimulatorConfig.from_dict(config.to_dict())
    assert restored.seed == 17
    assert restored.boundary_mode is BoundaryMode.FIXED


def test_public_lifegrid_namespace_exposes_v4_modules() -> None:
    import lifegrid
    from lifegrid.automata import ConwayGameOfLife
    from lifegrid.core import simulator as simulator_module
    from lifegrid.io import RLEParser
    from lifegrid.plugins import PluginManager

    assert lifegrid.__version__ == "4.0.0"
    assert lifegrid.automata is not None
    assert lifegrid.core is not None
    assert lifegrid.io is not None
    assert lifegrid.plugins is not None
    assert ConwayGameOfLife is not None
    assert simulator_module.Simulator is Simulator
    assert RLEParser is not None
    assert PluginManager is not None


def test_public_namespace_exposes_version() -> None:
    import lifegrid

    assert lifegrid.__version__ == "4.0.0"


def test_public_package_exposes_core_symbols() -> None:
    import lifegrid

    assert callable(lifegrid.Simulator)
    assert lifegrid.BoundaryMode.WRAP.value == "wrap"
    assert lifegrid.SimulatorConfig is not None
    assert callable(lifegrid.convolve_with_boundary)
    assert callable(lifegrid.roll_with_boundary)


def test_boundary_mode_exposes_alias_metadata() -> None:
    assert "toroidal" in BoundaryMode.aliases(BoundaryMode.WRAP)
    assert "fixed" in BoundaryMode.aliases(BoundaryMode.FIXED)
    assert "mirror" in BoundaryMode.aliases(BoundaryMode.REFLECT)


def test_public_boundary_registry_supports_mode_discovery() -> None:
    from lifegrid.core import list_boundary_modes

    registry = list_boundary_modes()
    assert {entry["name"] for entry in registry} == {"wrap", "fixed", "reflect"}
    assert any("toroidal" in entry["aliases"] for entry in registry)


def test_public_lifegrid_boundaries_module_is_available() -> None:
    from lifegrid.boundaries import BoundaryMode, list_boundary_modes

    assert BoundaryMode.WRAP.value == "wrap"
    assert {entry["name"] for entry in list_boundary_modes()} == {"wrap", "fixed", "reflect"}


def test_public_lifegrid_scenario_and_pattern_modules_are_available() -> None:
    from lifegrid.patterns import PATTERN_DATA, get_pattern_description
    from lifegrid.scenarios import build_scenario, get_scenario_names

    assert "glider" in get_scenario_names()
    assert "Conway's Game of Life" in PATTERN_DATA
    assert get_pattern_description("Conway's Game of Life", "glider")
    assert build_scenario("glider", 8, 8).shape == (8, 8)


def test_public_lifegrid_core_module_exports_are_available() -> None:
    from lifegrid.boundary import BoundaryMode
    from lifegrid.config import SimulatorConfig
    from lifegrid.simulator import Simulator

    assert BoundaryMode.WRAP.value == "wrap"
    assert SimulatorConfig is not None
    assert Simulator is not None


def test_public_lifegrid_root_exposes_scenario_helpers() -> None:
    import lifegrid

    assert callable(lifegrid.build_scenario)
    assert callable(lifegrid.get_scenario_names)
    assert "glider" in lifegrid.get_scenario_names()
    assert callable(lifegrid.get_pattern_description)


def test_public_lifegrid_management_modules_are_available() -> None:
    from lifegrid.autosave_manager import AutoSaveManager
    from lifegrid.config_manager import AppConfig
    from lifegrid.export_manager import ExportManager

    assert AutoSaveManager is not None
    assert AppConfig is not None
    assert ExportManager is not None


def test_public_core_namespace_exposes_boundary_helpers() -> None:
    from lifegrid.core import BoundaryMode, convolve_with_boundary, roll_with_boundary

    assert BoundaryMode.WRAP.value == "wrap"
    assert callable(convolve_with_boundary)
    assert callable(roll_with_boundary)


def test_snapshot_round_trip_preserves_state_and_reproducibility(tmp_path) -> None:
    simulator = Simulator(
        SimulatorConfig(width=10, height=10, seed=7, boundary_mode=BoundaryMode.FIXED)
    )
    simulator.initialize(pattern="Random Soup")
    simulator.step(2)
    path = tmp_path / "state.lifegrid.json"
    save_snapshot(simulator, path)

    restored = load_snapshot(path)
    assert restored.generation == simulator.generation
    assert restored.config.seed == 7
    assert restored.config.boundary_mode is BoundaryMode.FIXED
    np.testing.assert_array_equal(restored.get_grid(), simulator.get_grid())
    assert restored.metrics_log == simulator.metrics_log


def test_snapshot_restore_accepts_legacy_alias_boundary_names() -> None:
    simulator = Simulator(
        SimulatorConfig(width=8, height=8, seed=3, boundary_mode=BoundaryMode.WRAP)
    )
    simulator.initialize(pattern="Glider")
    payload = snapshot_dict(simulator)
    payload["config"]["boundary_mode"] = "wrap-around"
    payload.pop("automaton_state", None)
    payload.pop("rng_state", None)

    restored = load_snapshot_dict(payload)
    assert restored.config.boundary_mode is BoundaryMode.WRAP
    assert restored.generation == simulator.generation
    np.testing.assert_array_equal(restored.get_grid(), simulator.get_grid())


def test_autosave_uses_versioned_simulator_snapshots(tmp_path) -> None:
    simulator = Simulator(SimulatorConfig(width=8, height=8, seed=3))
    simulator.initialize(pattern="Random Soup")
    simulator.step()
    manager = AutoSaveManager(save_dir=str(tmp_path), max_backups=2)
    path = manager.save_simulator(simulator)
    assert path.exists()
    restored = manager.load_latest_simulator()
    assert restored is not None
    assert restored.generation == simulator.generation
    np.testing.assert_array_equal(restored.get_grid(), simulator.get_grid())


def test_autosave_keeps_only_configured_backup_count(tmp_path) -> None:
    simulator = Simulator(SimulatorConfig(width=8, height=8, seed=3))
    simulator.initialize(pattern="Empty")
    manager = AutoSaveManager(save_dir=str(tmp_path), max_backups=2)
    for _ in range(3):
        manager.save_simulator(simulator)
    assert len(manager.list_autosaves()) == 2
    assert not list(tmp_path.glob("*.tmp"))


def test_ant_snapshot_preserves_position_and_continuation(tmp_path) -> None:
    first = Simulator(SimulatorConfig(width=12, height=12))
    first.initialize(mode="Langton's Ant", pattern="Empty")
    first.step(5)
    path = tmp_path / "ant.json"
    save_snapshot(first, path)

    restored = load_snapshot(path)
    expected = first.get_grid().copy()
    first.step()
    restored.step()
    np.testing.assert_array_equal(restored.get_grid(), first.get_grid())
    assert not np.array_equal(expected, first.get_grid())


def test_snapshot_rejects_invalid_state_values(tmp_path) -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    path = tmp_path / "invalid.json"
    save_snapshot(simulator, path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["grid"][0][0] = 99
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="states outside range"):
        load_snapshot(path)


def test_ant_metrics_ignore_renderer_marker_state() -> None:
    simulator = Simulator(SimulatorConfig(width=8, height=8))
    simulator.initialize(mode="Langton's Ant", pattern="Empty")
    metrics = simulator.step()[0]
    assert metrics["population"] == 1
    assert "2" not in metrics["state_counts"]


def test_simulator_exposes_raw_grid_separately_from_display_grid() -> None:
    simulator = Simulator(SimulatorConfig(width=8, height=8))
    simulator.initialize(mode="Langton's Ant", pattern="Empty")
    display = simulator.get_grid()
    raw = simulator.get_raw_grid()
    assert 2 in display
    assert 2 not in raw


def test_gui_transition_metrics_use_raw_ant_grid() -> None:
    from gui.state import SimulationState
    from automata import LangtonsAnt

    automaton = LangtonsAnt(8, 8)
    previous = automaton.grid.copy()
    automaton.step()
    state = SimulationState()
    state.record_transition(
        previous, automaton.grid, 1, automaton.get_state_count()
    )
    state.update_population_stats(automaton.get_grid())
    assert state.metrics_log[-1]["state_counts"].get("2", 0) == 0


def test_cli_can_save_versioned_snapshot(tmp_path) -> None:
    snapshot = tmp_path / "run.lifegrid.json"
    assert main([
        "--steps", "2", "--seed", "5", "--quiet",
        "--snapshot", str(snapshot),
    ]) == 0
    restored = load_snapshot(snapshot)
    assert restored.generation == 2
    assert restored.config.seed == 5


def test_cli_can_resume_snapshot(tmp_path) -> None:
    initial = tmp_path / "initial.lifegrid.json"
    resumed = tmp_path / "resumed.lifegrid.json"
    assert main([
        "--steps", "1", "--seed", "5", "--quiet",
        "--snapshot", str(initial),
    ]) == 0
    assert main([
        "--load-snapshot", str(initial), "--steps", "1", "--quiet",
        "--snapshot", str(resumed),
    ]) == 0
    assert load_snapshot(resumed).generation == 2


def test_cli_resume_export_uses_snapshot_configuration(tmp_path) -> None:
    initial = tmp_path / "initial.lifegrid.json"
    output = tmp_path / "resumed.json"
    assert main([
        "--width", "9", "--height", "7", "--boundary", "fixed",
        "--seed", "5", "--steps", "1", "--quiet",
        "--snapshot", str(initial),
    ]) == 0
    assert main([
        "--load-snapshot", str(initial), "--steps", "1", "--quiet",
        "--export", str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["width"] == 9
    assert payload["height"] == 7
    assert payload["boundary"] == "fixed"
    assert payload["seed"] == 5


def test_cli_can_stop_on_cycle_and_records_reason(tmp_path) -> None:
    output = tmp_path / "cycle.json"
    assert main([
        "--steps", "20", "--pattern", "Block", "--stop-on-cycle", "--quiet",
        "--export", str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["stop_reason"] == "cycle_detected"
    assert payload["steps"] == 1
    assert payload["cycle_period"] == 1


def test_cli_cycle_state_limit_is_accepted(tmp_path) -> None:
    output = tmp_path / "limited.json"
    assert main([
        "--steps", "2", "--max-cycle-states", "2", "--quiet",
        "--export", str(output),
    ]) == 0


def test_cli_csv_export_serializes_state_counts(tmp_path) -> None:
    output = tmp_path / "metrics.csv"
    assert main([
        "--mode", "wireworld", "--steps", "1", "--seed", "2", "--quiet",
        "--export", str(output),
    ]) == 0
    csv_rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert "state_counts" in csv_rows[0]
    assert isinstance(json.loads(csv_rows[0]["state_counts"]), dict)


def test_cli_json_export_includes_metrics_summary(tmp_path) -> None:
    output = tmp_path / "state.json"
    assert main([
        "--steps", "1", "--pattern", "Block", "--quiet",
        "--export", str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metrics_summary"]["generations"] == 1
    assert payload["final_state_counts"]["1"] == 4


def test_cli_creates_nested_output_directories(tmp_path) -> None:
    output = tmp_path / "nested" / "results" / "state.json"
    assert main(["--steps", "0", "--quiet", "--export", str(output)]) == 0
    assert output.exists()


def test_cli_rejects_unknown_mode() -> None:
    assert main(["--mode", "not-a-mode", "--steps", "1", "--quiet"]) == 1


def test_cli_seed_reproduces_random_soup(tmp_path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    args = [
        "--mode", "conway", "--width", "12", "--height", "12",
        "--steps", "2", "--seed", "1234", "--quiet",
    ]
    assert main([*args, "--export", str(first)]) == 0
    assert main([*args, "--export", str(second)]) == 0
    assert first.read_text(encoding="utf-8") == second.read_text(
        encoding="utf-8"
    )


def test_simulators_own_independent_seeded_rngs() -> None:
    configs = [
        SimulatorConfig(width=12, height=12, seed=99),
        SimulatorConfig(width=12, height=12, seed=99),
    ]
    simulators = [Simulator(config) for config in configs]
    for simulator in simulators:
        simulator.initialize(pattern="Random Soup")
    np.testing.assert_array_equal(
        simulators[0].get_grid(), simulators[1].get_grid()
    )


def test_cli_diagnostics_exits_without_simulation(capsys) -> None:
    assert main(["--diagnostics"]) == 0
    output = capsys.readouterr().out
    assert "LifeGrid diagnostics" in output
    assert "patterns: available" in output


def test_undo_restores_state_and_redo_reapplies_step() -> None:
    simulator = Simulator(SimulatorConfig(width=10, height=10))
    simulator.initialize(pattern="Block")
    before = simulator.get_grid().copy()
    simulator.step()
    after = simulator.get_grid().copy()

    assert simulator.undo()
    assert simulator.generation == 0
    np.testing.assert_array_equal(simulator.get_grid(), before)
    assert simulator.redo()
    assert simulator.generation == 1
    np.testing.assert_array_equal(simulator.get_grid(), after)


def test_metrics_include_transitions_and_state_counts() -> None:
    simulator = Simulator(SimulatorConfig(width=8, height=8))
    simulator.initialize(pattern="Blinker")

    metrics = simulator.step()[0]

    assert metrics["generation"] == 1
    assert metrics["births"] == 2
    assert metrics["deaths"] == 2
    assert metrics["state_counts"]["0"] == 61
    assert metrics["state_counts"]["1"] == 3


def test_shared_metrics_reject_invalid_grid_shapes() -> None:
    with pytest.raises(ValueError, match="same shape"):
        calculate_transition_metrics(
            np.zeros((2, 2)), np.zeros((3, 3)), 1, 2
        )


def test_empty_metrics_summary_has_stable_schema() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    summary = simulator.get_metrics_summary()
    assert summary["undo_available"] is False
    assert summary["redo_available"] is False
    assert summary["births"] == 0
    assert summary["state_counts"]["0"] == 16
    assert summary["current_population"] == 0


def test_gui_state_accepts_shared_transition_metrics() -> None:
    from gui.state import SimulationState

    state = SimulationState()
    state.generation = 1
    state.record_transition(
        np.zeros((3, 3), dtype=int),
        np.array([[1, 1, 0], [0, 0, 0], [0, 0, 0]]),
        1,
        2,
    )
    state.update_population_stats(
        np.array([[1, 1, 0], [0, 0, 0], [0, 0, 0]])
    )
    assert state.metrics_log[-1]["births"] == 2


def test_gui_state_records_unchanged_population_each_generation() -> None:
    from gui.state import SimulationState

    state = SimulationState()
    empty = np.zeros((4, 4), dtype=int)
    state.update_population_stats(empty)
    state.generation = 1
    state.update_population_stats(empty)
    assert list(state.population_history) == [0, 0]
    assert state.metrics_log[-1]["delta"] == 0


def test_gui_csv_export_preserves_transition_metrics() -> None:
    from gui.state import SimulationState

    state = SimulationState()
    state.metrics_log.append(
        {
            "generation": 1,
            "population": 2,
            "births": 2,
            "deaths": 0,
            "state_counts": {"0": 14, "1": 2},
        }
    )
    csv_output = state.export_metrics_csv()
    assert "births" in csv_output
    assert "deaths" in csv_output
    rows = list(csv.DictReader(StringIO(csv_output)))
    assert json.loads(rows[0]["state_counts"]) == {"0": 14, "1": 2}
    assert "2" in csv_output


def test_gui_display_refresh_does_not_duplicate_metrics() -> None:
    from gui.state import SimulationState

    state = SimulationState()
    empty = np.zeros((4, 4), dtype=int)
    state.update_population_stats(empty)
    state.update_population_stats(empty, record=False)
    assert len(state.population_history) == 1
    assert len(state.metrics_log) == 1


def test_gui_external_grid_replacement_resets_runtime_history() -> None:
    from gui.state import SimulationState

    state = SimulationState()
    state.generation = 4
    state.metrics_log.append({"generation": 4})
    replacement = np.zeros((3, 3), dtype=int)
    replacement[1, 1] = 1
    state.reset_after_grid_replacement(replacement)
    assert state.generation == 0
    assert state.metrics_log == []
    assert len(state.grid_history) == 1
    np.testing.assert_array_equal(state.grid_history[0], replacement)


def test_gui_state_save_load_restores_grid(tmp_path) -> None:
    from automata import ConwayGameOfLife
    from gui.state import SimulationState

    state = SimulationState(current_automaton=ConwayGameOfLife(4, 4))
    state.current_automaton.grid[1, 2] = 1
    path = tmp_path / "gui-state.json"
    state.save_state(str(path))

    restored = SimulationState(current_automaton=ConwayGameOfLife(4, 4))
    restored.load_state(str(path))
    np.testing.assert_array_equal(
        restored.current_automaton.grid, state.current_automaton.grid
    )


def test_cycle_detection_reports_still_life() -> None:
    simulator = Simulator(SimulatorConfig(width=10, height=10))
    simulator.initialize(pattern="Block")
    simulator.step()

    summary = simulator.get_metrics_summary()
    assert summary["cycle_detected"] is True
    assert summary["cycle_start"] == 0
    assert summary["cycle_period"] == 1


def test_cycle_detection_history_is_bounded() -> None:
    simulator = Simulator(
        SimulatorConfig(width=10, height=10, max_cycle_states=2)
    )
    simulator.initialize(pattern="Random Soup")
    simulator.step(5)
    assert len(simulator._seen_states) <= 2


def test_cycle_detection_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_cycle_states"):
        Simulator(SimulatorConfig(max_cycle_states=0))


def test_simulator_config_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="width and height"):
        SimulatorConfig(width=0)


def test_simulator_config_normalizes_boundary_strings() -> None:
    config = SimulatorConfig(boundary_mode="fixed")
    assert config.boundary_mode is BoundaryMode.FIXED


def test_simulator_rejects_negative_step_counts() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    with pytest.raises(ValueError, match="num_steps"):
        simulator.step(-1)


def test_simulator_rejects_invalid_cell_states() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(mode="Wireworld", pattern="Empty")
    with pytest.raises(ValueError, match="Cell value"):
        simulator.set_cell(1, 1, 4)


def test_simulator_edit_starts_a_new_history_branch() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    simulator.step()
    simulator.set_cell(1, 1, 1)
    assert simulator.generation == 0
    assert simulator.metrics_log == []
    assert simulator.undo() is False


def test_simulator_reports_memory_estimate() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    assert simulator.estimate_memory_bytes() == 4 * 4 * 8


def test_undo_manager_reports_snapshot_memory() -> None:
    from core.undo_manager import UndoManager

    manager = UndoManager()
    manager.push_state("grid", np.zeros((2, 2), dtype=int))
    assert manager.memory_bytes() == 2 * 2 * 8


def test_rle_round_trip_preserves_binary_grid() -> None:
    original = np.zeros((4, 5), dtype=int)
    original[0, 1] = 1
    original[1, 2] = 1
    original[2, 0:3] = 1

    rle = RLEEncoder.encode(original)
    decoded, metadata = RLEParser.parse(rle)

    np.testing.assert_array_equal(decoded, original)
    assert metadata["x"] == "5"
    assert metadata["y"] == "4"
    assert metadata["rule"] == "B3/S23"


def test_export_manager_writes_json_and_png(tmp_path) -> None:
    grid = np.zeros((3, 3), dtype=int)
    grid[1, 1] = 1
    exporter = ExportManager()

    json_path = tmp_path / "state.json"
    png_path = tmp_path / "state.png"
    assert exporter.export_json(str(json_path), grid, {"generation": 2})
    assert exporter.export_png(grid, str(png_path), cell_size=2)
    assert json_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_plugin_manager_loads_included_plugin() -> None:
    manager = PluginManager()
    assert manager.load_plugins_from_directory("plugins") == 1
    automaton = manager.create_automaton("Day & Night", 8, 8)
    assert automaton is not None
    assert automaton.get_grid().shape == (8, 8)
    from api.app import list_modes

    assert any(entry["name"] == "Day & Night" for entry in list_modes())
    day_night = next(
        entry for entry in list_modes() if entry["name"] == "Day & Night"
    )
    assert day_night["source"] == "plugin"
    assert day_night["api_version"] == 1
    assert day_night["capabilities"]["patterns"] is True


def test_plugin_manager_rejects_duplicate_names_and_aliases() -> None:
    manager = PluginManager()
    assert manager.load_plugins_from_directory("plugins") == 1
    assert manager.load_plugins_from_directory("plugins") == 0
    plugin = manager.get_plugin("Day & Night")
    assert plugin is not None
    with pytest.raises(ValueError, match="already registered"):
        manager.register_plugin(plugin.__class__())

    from core.registry import ModeDescriptor, register_mode

    with pytest.raises(ValueError, match="already registered"):
        register_mode(
            ModeDescriptor(
                "Another Mode", "collision", None, aliases=("conway",)
            )
        )


def test_api_session_functions_create_and_step() -> None:
    response = create_session(
        CreateSessionRequest(
            width=8, height=6, mode="conway", boundary_mode="fixed", seed=42
        )
    )
    session_id = response["session_id"]

    from api.app import (
        delete_session, get_metrics, get_session, get_snapshot, get_state,
        list_sessions, reset_session, restore_session, step_session,
    )

    assert step_session(session_id, StepRequest(steps=2)) == {"generation": 2}
    state = get_state(session_id)
    assert state["generation"] == 2
    assert state["width"] == 8
    assert state["height"] == 6
    assert state["boundary_mode"] == "fixed"
    assert state["seed"] == 42
    metrics = get_metrics(session_id)
    assert metrics["generations"] == 2
    assert isinstance(metrics["cycle_detected"], bool)
    assert metrics["cycle_period"] == 1
    assert metrics["births"] == 0
    assert metrics["deaths"] == 0
    assert metrics["state_counts"]["0"] == 48
    snapshot = get_snapshot(session_id)
    assert snapshot["snapshot_version"] == 1
    assert snapshot["generation"] == 2
    restored_response = restore_session(snapshot)
    restored_state = get_state(restored_response["session_id"])
    assert restored_state["generation"] == 2
    assert restored_state["seed"] == 42
    listed = {entry["session_id"]: entry for entry in list_sessions()}
    assert listed[session_id]["mode"] == "Conway's Game of Life"
    assert listed[session_id]["generation"] == 2
    detail = get_session(session_id)
    assert detail["boundary_mode"] == "fixed"
    assert detail["metrics"]["generations"] == 2
    assert delete_session(restored_response["session_id"]) == {"status": "deleted"}
    assert reset_session(session_id) == {"generation": 0}
    assert delete_session(session_id) == {"status": "deleted"}


def test_api_mode_discovery_lists_canonical_modes() -> None:
    from api.app import list_modes

    modes = {entry["name"]: entry for entry in list_modes()}
    assert "Hexagonal Life" in modes
    assert "Custom Rules" in modes
    assert "conway" in modes["Conway's Game of Life"]["aliases"]


def test_api_pattern_discovery_lists_descriptions() -> None:
    from api.app import list_patterns

    patterns = list_patterns("conway")
    names = {pattern["name"] for pattern in patterns}
    assert "Glider" in names
    assert all("description" in pattern for pattern in patterns)


def test_api_boundary_discovery_lists_aliases() -> None:
    from api.app import list_boundaries

    boundaries = {entry["name"]: entry for entry in list_boundaries()}
    assert "wrap" in boundaries
    assert "toroidal" in boundaries["wrap"]["aliases"]
    assert "continuous" in boundaries["wrap"]["aliases"]


def test_api_diagnostics_reports_runtime_resources() -> None:
    from api.app import diagnostics

    payload = diagnostics()
    assert payload["status"] == "ok"
    assert payload["patterns_available"] is True
    assert payload["mode_count"] >= 10


def test_versioned_api_routes_are_registered() -> None:
    from api.app import app, v1_router

    assert any(
        getattr(route, "path", None) == "/modes"
        for route in v1_router.routes
    )
    assert any(
        getattr(route, "path", None) == "/session"
        for route in v1_router.routes
    )
    assert any(
        getattr(route, "path", None) == "/session/{session_id}/metrics"
        for route in v1_router.routes
    )
    assert any(
        getattr(route, "path", None) == "/session/{session_id}/stream"
        for route in v1_router.routes
    )
    assert app.version == "1.0.0"
    assert any(type(route).__name__ == "_IncludedRouter" for route in app.routes)


def test_api_rejects_unknown_modes_and_partial_rules() -> None:
    from api.app import HTTPException

    with pytest.raises(HTTPException) as unknown:
        create_session(CreateSessionRequest(mode="not-a-mode"))
    assert unknown.value.status_code == 400

    with pytest.raises(HTTPException) as partial:
        create_session(CreateSessionRequest(birth_rule="3"))
    assert partial.value.status_code == 400

    with pytest.raises(HTTPException) as boundary:
        create_session(CreateSessionRequest(boundary_mode="invalid"))
    assert boundary.value.status_code == 400


def test_api_exposes_positive_session_capacity() -> None:
    from api.app import MAX_SESSIONS

    assert MAX_SESSIONS >= 1


def test_api_pattern_load_resets_simulation_history() -> None:
    from api.app import PatternRequest, get_metrics, load_pattern, step_session

    session_id = create_session(CreateSessionRequest(width=8, height=8))["session_id"]
    step_session(session_id, StepRequest(steps=2))
    assert load_pattern(session_id, PatternRequest(pattern_name="Glider")) == {
        "status": "ok"
    }
    assert get_metrics(session_id)["generations"] == 0


def test_api_rejects_unknown_pattern() -> None:
    from api.app import PatternRequest, HTTPException, load_pattern

    session_id = create_session(CreateSessionRequest(width=8, height=8))["session_id"]
    with pytest.raises(HTTPException) as error:
        load_pattern(session_id, PatternRequest(pattern_name="not-a-pattern"))
    assert error.value.status_code == 400


def test_simulator_public_grid_replacement_resets_history() -> None:
    simulator = Simulator(SimulatorConfig(width=4, height=4))
    simulator.initialize(pattern="Empty")
    simulator.step()
    replacement = np.zeros((4, 4), dtype=int)
    replacement[1, 1] = 1
    simulator.replace_grid(replacement)
    assert simulator.generation == 0
    assert simulator.metrics_log == []
    np.testing.assert_array_equal(simulator.get_raw_grid(), replacement)