#!/usr/bin/env python3
"""Command-line interface for headless LifeGrid simulation.

Usage examples:
    python src/cli.py --mode conway --steps 100 --export out.gif
    python src/cli.py --mode "Brian's Brain" --width 200 --height 200 \
        --steps 500 --export video.mp4 --fps 30
    python src/cli.py --rule B36/S23 --pattern "Random Soup" --steps 1000 \
        --export stats.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np

# Ensure src/ is on path when run directly
_src = str(Path(__file__).resolve().parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from core.simulator import Simulator  # noqa: E402
from core.config import SimulatorConfig  # noqa: E402
from core.boundary import BOUNDARY_ALIASES, BoundaryMode  # noqa: E402
from core.registry import normalize_mode  # noqa: E402
from core.registry import iter_modes  # noqa: E402
from core.snapshot import load_snapshot, save_snapshot  # noqa: E402
from plugin_system import PluginManager  # noqa: E402
from patterns import PATTERN_DATA  # noqa: E402
from automata import parse_bs  # noqa: E402
from scenarios import build_scenario  # noqa: E402


def _positive_int(value: str) -> int:
    """Parse a command-line integer that must be greater than zero."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _nonnegative_int(value: str) -> int:
    """Parse a command-line integer that may be zero but not negative."""
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _boundary_mode(value: str) -> BoundaryMode:
    """Parse a boundary mode for CLI configuration."""
    try:
        return BoundaryMode.from_string(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _resolve_mode(name: str) -> str:
    """Resolve a user-supplied mode string to its canonical name."""
    return normalize_mode(name)


def _dependency_version(name: str) -> str:
    """Return an installed dependency version or ``missing``."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def _print_diagnostics() -> None:
    """Print runtime, dependency, resource, GPU, and plugin diagnostics."""
    patterns_path = Path(__file__).resolve().parent / "data" / "patterns.json"
    plugins_path = Path.cwd() / "plugins"
    try:
        from plugin_system import PluginManager

        plugin_manager = PluginManager()
        plugin_count = plugin_manager.load_plugins_from_directory(
            str(plugins_path)
        ) if plugins_path.is_dir() else 0
    except Exception:  # pragma: no cover - diagnostics must not crash startup
        plugin_count = "error"

    try:
        from performance.gpu import is_gpu_available

        gpu_status = "available" if is_gpu_available() else "unavailable"
    except Exception:  # pragma: no cover - optional backend
        gpu_status = "unavailable"

    print(f"LifeGrid diagnostics (Python {platform.python_version()})")
    print(f"platform: {platform.platform()}")
    print(f"numpy: {_dependency_version('numpy')}")
    print(f"scipy: {_dependency_version('scipy')}")
    print(f"pillow: {_dependency_version('Pillow')}")
    print(f"imageio: {_dependency_version('imageio')}")
    print(f"tkinter: {'available' if importlib.util.find_spec('tkinter') else 'missing'}")
    print(f"patterns: {'available' if patterns_path.is_file() else 'missing'}")
    print(f"plugins: {plugin_count}")
    print(f"gpu: {gpu_status}")


def _load_plugins() -> int:
    """Load plugins from the current project's plugins directory."""
    plugin_dir = Path.cwd() / "plugins"
    if not plugin_dir.is_dir():
        return 0
    return PluginManager().load_plugins_from_directory(str(plugin_dir))


def _export_png(
    grid: np.ndarray, path: str, cell_size: int = 4
) -> None:
    try:
        from PIL import Image as PILImage
    except ImportError:
        print("Error: PNG export requires Pillow (pip install pillow).")
        sys.exit(1)

    h, w = grid.shape
    img = PILImage.new("RGB", (w * cell_size, h * cell_size), "white")
    pixels = img.load()
    if pixels is None:
        return
    for y in range(h):
        for x in range(w):
            if grid[y, x]:
                for dy in range(cell_size):
                    for dx in range(cell_size):
                        pixels[x * cell_size + dx, y * cell_size + dy] = (
                            0, 0, 0,
                        )
    img.save(path)


def _export_gif(
    grids: list[np.ndarray], path: str, fps: int, cell_size: int = 4
) -> None:
    try:
        from PIL import Image as PILImage
    except ImportError:
        print("Error: GIF export requires Pillow (pip install pillow).")
        sys.exit(1)

    frames = []
    for grid in grids:
        h, w = grid.shape
        img = PILImage.new("RGB", (w * cell_size, h * cell_size), "white")
        pixels = img.load()
        if pixels is None:
            continue
        for y in range(h):
            for x in range(w):
                if grid[y, x]:
                    for dy in range(cell_size):
                        for dx in range(cell_size):
                            pixels[
                                x * cell_size + dx, y * cell_size + dy
                            ] = (0, 0, 0)
        frames.append(img)
    if frames:
        duration = max(10, 1000 // fps)
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
        )


def _export_video(
    grids: list[np.ndarray], path: str, fps: int, cell_size: int = 4
) -> None:
    try:
        import imageio
    except ImportError:
        print("Error: Video export requires imageio (pip install imageio).")
        sys.exit(1)

    images: list[np.ndarray] = []
    for grid in grids:
        h, w = grid.shape
        frame = np.full((h * cell_size, w * cell_size, 3), 255, dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                if grid[y, x]:
                    frame[
                        y * cell_size : (y + 1) * cell_size,
                        x * cell_size : (x + 1) * cell_size,
                    ] = 0
        images.append(frame)
    if images:
        imageio.mimsave(
            path, images, fps=fps,  # type: ignore[arg-type]
        )


def _export_csv(metrics: list[dict], path: str) -> None:
    if not metrics:
        print("No metrics to export.")
        return
    keys = list(metrics[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True)
                    if isinstance(value, (dict, list, tuple))
                    else value
                    for key, value in metric.items()
                }
            )

def _ensure_parent_directory(path: str) -> None:
    """Create an output parent directory when one is specified."""
    parent = Path(path).expanduser().parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lifegrid",
        description="LifeGrid — headless cellular automaton simulator",
    )
    p.add_argument(
        "--mode", "-m",
        default="conway",
        help="Automaton mode (conway, highlife, wireworld, etc.)",
    )
    p.add_argument(
        "--rule",
        default=None,
        help="Custom B/S rule, e.g. B36/S23 (overrides --mode)",
    )
    p.add_argument("--width", "-W", type=_positive_int, default=100)
    p.add_argument("--height", "-H", type=_positive_int, default=100)
    p.add_argument(
        "--steps", "-n", type=_nonnegative_int, default=100,
        help="Number of generations to simulate",
    )
    p.add_argument("--pattern", "-p", default="Random Soup")
    p.add_argument(
        "--scenario",
        default=None,
        help="Load a named scenario preset such as blinker or glider",
    )
    p.add_argument(
        "--boundary", default="wrap", type=_boundary_mode,
        help=(
            "Boundary mode: wrap / toroidal / wrap-around / continuous / periodic "
            "(or fixed / fill / reflect / mirror)"
        ),
    )
    p.add_argument(
        "--seed", type=_nonnegative_int, default=None,
        help="Seed NumPy randomness for reproducible procedural patterns",
    )
    p.add_argument(
        "--export", "-o",
        default=None,
        help="Output path (.png, .gif, .mp4, .webm, .csv, .json)",
    )
    p.add_argument(
        "--snapshot", default=None,
        help="Save a versioned replayable simulator snapshot",
    )
    p.add_argument(
        "--load-snapshot", default=None,
        help="Resume from a versioned simulator snapshot",
    )
    p.add_argument(
        "--fps", type=_positive_int, default=10, help="Frames per second"
    )
    p.add_argument(
        "--cell-size", type=_positive_int, default=4,
        help="Cell size in pixels for image/video exports",
    )
    p.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress progress output",
    )
    p.add_argument(
        "--snapshot-every", type=_positive_int, default=1,
        help="Capture frame every N steps (for GIF/video)",
    )
    p.add_argument(
        "--diagnostics", action="store_true",
        help="Print environment and resource diagnostics, then exit",
    )
    p.add_argument(
        "--stop-on-cycle", action="store_true",
        help="Stop early when a repeated grid state is detected",
    )
    p.add_argument(
        "--max-cycle-states", type=_positive_int, default=10000,
        help="Maximum cycle fingerprints retained in memory",
    )
    p.add_argument(
        "--list-modes", action="store_true",
        help="List canonical modes and aliases, then exit",
    )
    p.add_argument(
        "--list-patterns", action="store_true",
        help="List patterns for --mode, then exit",
    )
    p.add_argument(
        "--list-boundaries", action="store_true",
        help="List boundary modes and aliases, then exit",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Run the headless simulator."""
    args = _build_parser().parse_args(argv)

    if args.diagnostics:
        _print_diagnostics()
        return 0

    if args.list_modes:
        _load_plugins()
        for descriptor in iter_modes():
            aliases = ", ".join(descriptor.aliases) or "none"
            print(f"{descriptor.name}: {aliases}")
        return 0

    if args.list_patterns:
        _load_plugins()
        try:
            mode = _resolve_mode(args.mode)
        except ValueError as exc:
            print(f"Pattern listing error: {exc}", file=sys.stderr)
            return 1
        for name, (_, description) in PATTERN_DATA.get(mode, {}).items():
            print(f"{name}: {description}")
        return 0

    if args.list_boundaries:
        for member in BoundaryMode:
            aliases = BOUNDARY_ALIASES.get(member.value, [])
            alias_text = ", ".join(aliases) if aliases else "none"
            print(f"{member.value}: {alias_text}")
        return 0

    birth_rule = None
    survival_rule = None

    try:
        _load_plugins()
        if args.load_snapshot:
            sim = load_snapshot(args.load_snapshot)
            mode = sim.config.automaton_mode
        else:
            mode = _resolve_mode(args.mode)
        if args.rule and not args.load_snapshot:
            birth_set, survival_set = parse_bs(args.rule)
            birth_rule = birth_set
            survival_rule = survival_set
            mode = "Custom Rules"

        if not args.load_snapshot:
            config = SimulatorConfig(
                width=args.width,
                height=args.height,
                automaton_mode=mode,
                birth_rule=birth_rule,
                survival_rule=survival_rule,
                boundary_mode=args.boundary,
                seed=args.seed,
                max_cycle_states=args.max_cycle_states,
            )
            sim = Simulator(config)
            if args.scenario:
                sim.initialize(mode=mode, pattern="Empty")
                sim.replace_grid(build_scenario(args.scenario, args.width, args.height))
            else:
                sim.initialize(mode=mode, pattern=args.pattern)
    except (ValueError, RuntimeError) as exc:
        print(f"Initialization error: {exc}", file=sys.stderr)
        return 1

    grids: list[np.ndarray] = []
    all_metrics: list[dict] = []
    completed_steps = 0
    stop_reason = "completed"

    if not args.quiet:
        print(
            f"LifeGrid CLI — mode={mode}  size={args.width}x{args.height}  "
            f"steps={args.steps}"
        )

    for i in range(1, args.steps + 1):
        metrics_list = sim.step()
        completed_steps = i
        if metrics_list:
            all_metrics.extend(metrics_list)
        if i % args.snapshot_every == 0:
            grids.append(np.copy(sim.get_grid()))
        if not args.quiet and i % max(1, args.steps // 20) == 0:
            pop = int(np.count_nonzero(sim.get_grid()))
            print(f"  gen {i:>6d}  pop {pop:>6d}")
        if args.stop_on_cycle and sim.get_metrics_summary()["cycle_detected"]:
            stop_reason = "cycle_detected"
            break

    final_grid = sim.get_grid()

    if not args.quiet:
        pop = int(np.count_nonzero(final_grid))
        print(f"Done — final population: {pop}")

    # Export
    if args.export:
        _ensure_parent_directory(args.export)
        ext = Path(args.export).suffix.lower()
        if ext == ".png":
            _export_png(final_grid, args.export, args.cell_size)
        elif ext == ".gif":
            _export_gif(grids, args.export, args.fps, args.cell_size)
        elif ext in (".mp4", ".webm"):
            _export_video(grids, args.export, args.fps, args.cell_size)
        elif ext == ".csv":
            _export_csv(all_metrics, args.export)
        elif ext == ".json":
            metrics_summary = sim.get_metrics_summary()
            payload = {
                "mode": sim.config.automaton_mode,
                "width": sim.config.width,
                "height": sim.config.height,
                "steps": completed_steps,
                "boundary": sim.config.boundary_mode.value,
                "seed": sim.config.seed,
                "max_cycle_states": sim.config.max_cycle_states,
                "stop_reason": stop_reason,
                "cycle_start": sim.get_metrics_summary()["cycle_start"],
                "cycle_period": sim.get_metrics_summary()["cycle_period"],
                "final_population": int(np.count_nonzero(final_grid)),
                "final_state_counts": metrics_summary["state_counts"],
                "metrics_summary": metrics_summary,
                "grid": final_grid.tolist(),
            }
            with open(args.export, "w", encoding="utf-8") as f:
                json.dump(payload, f)
        else:
            print(f"Unknown export format: {ext}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Exported to {args.export}")

    if args.snapshot:
        _ensure_parent_directory(args.snapshot)
        save_snapshot(sim, args.snapshot)
        if not args.quiet:
            print(f"Saved snapshot to {args.snapshot}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
