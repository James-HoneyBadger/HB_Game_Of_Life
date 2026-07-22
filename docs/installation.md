# Installation

## System Requirements

- **Python** 3.11 or later
- **Tcl/Tk** — ships with most Python distributions; required for the GUI
- **Operating system** — Linux, macOS, or Windows

## Quick Install

```bash
git clone https://github.com/James-HoneyBadger/LifeGrid.git
cd LifeGrid
pip install -r requirements.txt
```

### Core Dependencies

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| numpy | 1.24.0 | Grid computation |
| scipy | 1.11.0 | Convolution for neighbor counting |
| Pillow | 10.0.0 | Image export (PNG, GIF) |
| imageio | 2.31.0 | Video export (MP4, WebM) |
| imageio-ffmpeg | 0.4.9 | FFmpeg backend for video |
| fastapi | — | REST & WebSocket API |
| uvicorn | — | ASGI server |
| httpx | — | HTTP client (used by tests) |

## Development Install

For contributors who need linting, formatting, type checking, and doc building:

```bash
make install-dev
```

This runs `pip install -e ".[dev,docs,export]"` which installs:

- **dev**: pytest, pytest-cov, flake8, pylint, mypy, black, isort
- **docs**: sphinx, sphinx-rtd-theme
- **export**: all image/video dependencies

## Optional: GPU Acceleration

LifeGrid supports CuPy for CUDA-accelerated simulations. This is entirely optional — the simulator falls back to NumPy when CuPy is unavailable.

```bash
# Match the package to your CUDA toolkit version
pip install cupy-cuda12x    # CUDA 12.x
pip install cupy-cuda11x    # CUDA 11.x
```

Verify GPU availability:

```python
from src.performance.gpu import is_gpu_available
print(is_gpu_available())  # True if CuPy + CUDA are working
```

## Building a Standalone Executable

```bash
make executable
```

This uses PyInstaller with the included `lifegrid.spec` to produce a single distributable binary.

## Verifying the Install

```bash
# Launch the GUI
python src/main.py

# Run the test suite
make test

# Run a quick CLI simulation
python src/cli.py --mode conway --steps 100 --quiet
```
