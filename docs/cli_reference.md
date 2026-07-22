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
| `--width` | `-W` | int | 64 | Grid width |
| `--height` | `-H` | int | 64 | Grid height |
| `--steps` | `-n` | int | 100 | Number of generations to simulate |
| `--cell-size` | | int | 4 | Cell size in pixels (for image/video export) |
| `--export` | `-o` | path | | Export file path. Format determined by extension. |
| `--fps` | | int | 10 | Frames per second (GIF, MP4, WebM) |
| `--snapshot-every` | | int | | Save a numbered PNG every N generations |
| `--quiet` | `-q` | flag | | Suppress progress output |

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

## Export Formats

The `--export` flag determines the output format by file extension:

| Extension | Output |
|-----------|--------|
| `.png` | Single PNG snapshot of the final grid |
| `.gif` | Animated GIF of all generations |
| `.mp4` | MP4 video |
| `.webm` | WebM video |
| `.csv` | CSV with per-generation statistics (generation, population, density) |
| `.json` | JSON grid state of the final generation |

## Examples

### Basic simulation

```bash
python src/cli.py --mode conway --steps 500
```

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
