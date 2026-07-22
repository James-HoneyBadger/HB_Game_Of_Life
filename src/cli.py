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
import json
import sys
from pathlib import Path

import numpy as np

# Ensure src/ is on path when run directly
_src = str(Path(__file__).resolve().parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from core.simulator import Simulator  # noqa: E402
from core.config import SimulatorConfig  # noqa: E402
from automata import parse_bs  # noqa: E402


# Canonical name lookup (case-insensitive convenience aliases)
_MODE_ALIASES: dict[str, str] = {
    "conway": "Conway's Game of Life",
    "highlife": "HighLife",
    "immigration": "Immigration",
    "rainbow": "Rainbow",
    "wireworld": "Wireworld",
    "briansbrain": "Brian's Brain",
    "brians brain": "Brian's Brain",
    "ant": "Langton's Ant",
    "generations": "Generations",
    "hexagonal": "Hexagonal Life",
}


def _resolve_mode(name: str) -> str:
    """Resolve a user-supplied mode string to its canonical name."""
    lower = name.lower().replace("_", " ").replace("-", " ")
    return _MODE_ALIASES.get(lower, name)


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
        writer.writerows(metrics)


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
    p.add_argument("--width", "-W", type=int, default=100)
    p.add_argument("--height", "-H", type=int, default=100)
    p.add_argument(
        "--steps", "-n", type=int, default=100,
        help="Number of generations to simulate",
    )
    p.add_argument("--pattern", "-p", default="Random Soup")
    p.add_argument(
        "--export", "-o",
        default=None,
        help="Output path (.png, .gif, .mp4, .webm, .csv, .json)",
    )
    p.add_argument("--fps", type=int, default=10, help="Frames per second")
    p.add_argument(
        "--cell-size", type=int, default=4,
        help="Cell size in pixels for image/video exports",
    )
    p.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress progress output",
    )
    p.add_argument(
        "--snapshot-every", type=int, default=1,
        help="Capture frame every N steps (for GIF/video)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Run the headless simulator."""
    args = _build_parser().parse_args(argv)

    birth_rule = None
    survival_rule = None
    mode = _resolve_mode(args.mode)

    if args.rule:
        birth_set, survival_set = parse_bs(args.rule)
        birth_rule = birth_set
        survival_rule = survival_set
        mode = "Custom Rules"

    config = SimulatorConfig(
        width=args.width,
        height=args.height,
        automaton_mode=mode,
        birth_rule=birth_rule,
        survival_rule=survival_rule,
    )

    sim = Simulator(config)

    try:
        sim.initialize(mode=mode, pattern=args.pattern)
    except (ValueError, RuntimeError) as exc:
        print(f"Initialization error: {exc}", file=sys.stderr)
        return 1

    grids: list[np.ndarray] = []
    all_metrics: list[dict] = []

    if not args.quiet:
        print(
            f"LifeGrid CLI — mode={mode}  size={args.width}x{args.height}  "
            f"steps={args.steps}"
        )

    for i in range(1, args.steps + 1):
        metrics_list = sim.step()
        if metrics_list:
            all_metrics.extend(metrics_list)
        if i % args.snapshot_every == 0:
            grids.append(np.copy(sim.get_grid()))
        if not args.quiet and i % max(1, args.steps // 20) == 0:
            pop = int(np.count_nonzero(sim.get_grid()))
            print(f"  gen {i:>6d}  pop {pop:>6d}")

    final_grid = sim.get_grid()

    if not args.quiet:
        pop = int(np.count_nonzero(final_grid))
        print(f"Done — final population: {pop}")

    # Export
    if args.export:
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
            payload = {
                "mode": mode,
                "width": args.width,
                "height": args.height,
                "steps": args.steps,
                "final_population": int(np.count_nonzero(final_grid)),
                "grid": final_grid.tolist(),
            }
            with open(args.export, "w", encoding="utf-8") as f:
                json.dump(payload, f)
        else:
            print(f"Unknown export format: {ext}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Exported to {args.export}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
