# CLI Reference

LifeGrid includes a headless CLI for running simulations without a GUI. It is useful for scripting, batch processing, and CI pipelines.

## Usage

```bash
python src/cli.py [OPTIONS]
```

## Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--mode` | `-m` | string | `conway` | Automaton mode (see aliases below) |
| `--rule` | | string | | Custom B/S rule string (e.g., `B36/S23`). Overrides `--mode`. |
| `--width` | `-W` | int | 100 | Grid width |
| `--height` | `-H` | int | 100 | Grid height |
| `--steps` | `-n` | int | 100 | Number of generations to simulate |
| `--pattern` | `-p` | string | `Random Soup` | Pattern name to load |
| `--scenario` | | string | | Named preset scenario such as `blinker`, `glider`, or `exploder` |
| `--boundary` | | string | `wrap` | Boundary mode: `wrap`, `fixed`, or `reflect` |
| `--seed` | | int | | Seed NumPy randomness for reproducible procedural patterns |
| `--cell-size` | | int | 4 | Cell size in pixels (for image/video export) |
| `--export` | `-o` | path | | Export file path. Format determined by extension. |
| `--snapshot` | | path | | Save a versioned replayable simulator snapshot. |
| `--load-snapshot` | | path | | Resume from a versioned simulator snapshot. |
| `--fps` | | int | 10 | Frames per second (GIF, MP4, WebM) |
| `--snapshot-every` | | int | | Save a numbered PNG every N generations |
| `--quiet` | `-q` | flag | | Suppress progress output |
| `--diagnostics` | | flag | | Print environment and resource diagnostics, then exit |
| `--stop-on-cycle` | | flag | | Stop early when a repeated grid state is detected |
| `--max-cycle-states` | | int | 10000 | Maximum retained cycle fingerprints |
| `--list-modes` | | flag | | List canonical modes and aliases, then exit |
| `--list-patterns` | | flag | | List patterns for `--mode`, then exit |

## Mode Aliases

| Alias | Automaton |
|-------|-----------|
| `conway` | Conway's Game of Life |
| `highlife` | HighLife |
| `immigration` | Immigration |
| `rainbow` | Rainbow |
| `wireworld` | Wireworld |
| `briansbrain` | Brian's Brain |
| `ant` | Langton's Ant |
| `generations` | Generations |
| `hexagonal` | Hexagonal Life |

Plugins in the project `plugins/` directory are loaded automatically, so a
plugin's canonical name can also be passed to `--mode`.

## Export Formats

The `--export` flag determines the output format by file extension. Missing
parent directories are created automatically:

| Extension | Output |
|-----------|--------|
| `.png` | Single PNG snapshot of the final grid |
| `.gif` | Animated GIF of all generations |
| `.mp4` | MP4 video |
| `.webm` | WebM video |
| `.csv` | CSV with per-generation statistics (generation, population, density) |
| `.json` | Final grid state, run metadata, and metrics summary |

## Examples

### Basic simulation

```bash
python src/cli.py --mode conway --steps 500
```

### Start from a named scenario preset

```bash
python src/cli.py --mode conway --scenario blinker --steps 100 --quiet
python src/cli.py --mode conway --scenario glider --width 120 --height 120 --steps 200
```

The built-in scenario presets currently include `blinker`, `glider`, `toad`, `beacon`, `lwss`, `exploder`, and `random`.

### Export an animated GIF

```bash
python src/cli.py --mode highlife --steps 1000 --export output/highlife.gif --fps 20
```

### Custom rule with video export

```bash
python src/cli.py --rule B36/S23 --steps 2000 -W 128 -H 128 --export output/custom.mp4 --fps 30
```

### CSV statistics

```bash
python src/cli.py --mode briansbrain --steps 500 --export output/stats.csv --quiet
```

### Periodic snapshots

```bash
python src/cli.py --mode wireworld --steps 1000 --snapshot-every 100 --export output/frames/snap.png
```

This creates `snap_0000.png`, `snap_0100.png`, `snap_0200.png`, etc.

### Silent batch run

```bash
for mode in conway highlife briansbrain; do
    python src/cli.py --mode $mode --steps 500 --export output/${mode}.gif --quiet
done
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments or export failure |
