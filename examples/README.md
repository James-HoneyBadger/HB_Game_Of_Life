# Examples

Example scripts demonstrating LifeGrid's Python API for scripting, analysis, and automation.

## Files

| Script | Description |
|--------|-------------|
| `enhanced_statistics_examples.py` | Calculate entropy, complexity, fractal dimension, connected components, cluster statistics, symmetry, center of mass, and radial distribution on simulation grids. |
| `pattern_management_examples.py` | Use `PatternManager` to save, search, tag, and retrieve patterns with favorites and history. |
| `ui_enhancement_examples.py` | Demonstrate theme management, tool configuration, and UI customization via the Python API. |
| `video_export_examples.py` | Run a simulation and export the results as PNG, GIF, MP4, and WebM using `ExportManager`. |

## Running

```bash
# Run all examples
make examples

# Run a single example
python examples/video_export_examples.py
```

## Prerequisites

All examples require the project dependencies (`pip install -r requirements.txt`). Video export examples additionally require `imageio` and `imageio-ffmpeg` (included in the default requirements).
