#!/usr/bin/env python3
"""Application entry point for the cellular automaton simulator."""

from __future__ import annotations

import importlib.util
import sys


def check_dependencies() -> None:
    """Verify that all required Python packages are installed."""
    missing = []

    if importlib.util.find_spec("tkinter") is None:
        missing.append("tkinter (usually bundled with Python)")

    if importlib.util.find_spec("numpy") is None:
        missing.append("numpy")

    if importlib.util.find_spec("scipy") is None:
        missing.append("scipy")

    if importlib.util.find_spec("PIL") is None:
        missing.append("Pillow")

    if missing:
        print("Error: Missing required Python packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install them using:")
        print("  pip install -r requirements.txt")
        print(
            "\nFor tkinter, ensure you have Python with Tk support "
            "installed."
        )
        sys.exit(1)


def main() -> None:
    """Start the Tkinter event loop."""
    check_dependencies()
    # pylint: disable=import-outside-toplevel
    from gui.app import launch

    launch()


if __name__ == "__main__":
    main()
