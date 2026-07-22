"""Auto-save functionality for LifeGrid.

Provides automatic saving of simulation state at regular intervals
and crash recovery capabilities.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

import numpy as np


class AutoSaveManager:
    """Manages automatic saving of simulation state.

    Args:
        save_dir: Directory to store auto-save files
        interval: Auto-save interval in seconds (default: 300 = 5 minutes)
        max_backups: Maximum number of auto-save files to keep
    """

    def __init__(
        self,
        save_dir: str = "autosave",
        interval: int = 300,
        max_backups: int = 5,
    ) -> None:
        """Initialize auto-save manager."""
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        self.interval = interval
        self.max_backups = max_backups

        self.enabled = False
        self.last_save_time = 0.0
        self._timer: Optional[threading.Timer] = None
        self._save_callback: Optional[Callable[[], dict]] = None

    def set_save_callback(self, callback: Callable[[], dict]) -> None:
        """Set callback function to get state data.

        The callback should return a dictionary with the state to save.

        Args:
            callback: Function that returns state dictionary
        """
        self._save_callback = callback

    def start(self) -> None:
        """Start auto-save timer."""
        if not self.enabled:
            self.enabled = True
            self._schedule_save()

    def stop(self) -> None:
        """Stop auto-save timer."""
        self.enabled = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_save(self) -> None:
        """Schedule next auto-save."""
        if not self.enabled:
            return

        self._timer = threading.Timer(self.interval, self._perform_save)
        self._timer.daemon = True
        self._timer.start()

    def _perform_save(self) -> None:
        """Perform auto-save operation."""
        if not self._save_callback:
            self._schedule_save()
            return

        try:
            state = self._save_callback()
            self._save_state(state)
            self.last_save_time = time.time()
        except Exception:  # pylint: disable=broad-except
            # Continue even if save fails
            pass

        # Schedule next save
        self._schedule_save()

    def _save_state(self, state: dict) -> None:
        """Save state to file.

        Args:
            state: State dictionary to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"autosave_{timestamp}.json"
        filepath = self.save_dir / filename

        # Convert numpy arrays to lists for JSON serialization
        serializable_state = self._make_serializable(state)

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, indent=2)

        # Clean up old backups
        self._cleanup_old_backups()

    def _make_serializable(self, obj):
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        return obj

    def _cleanup_old_backups(self) -> None:
        """Remove old auto-save files beyond max_backups."""
        autosave_files = sorted(
            self.save_dir.glob("autosave_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Remove excess files
        for old_file in autosave_files[self.max_backups :]:
            try:
                old_file.unlink()
            except OSError:
                pass

    def get_latest_autosave(self) -> Optional[Path]:
        """Get path to most recent auto-save file.

        Returns:
            Path to latest auto-save, or None if none exist
        """
        autosave_files = sorted(
            self.save_dir.glob("autosave_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if autosave_files:
            return autosave_files[0]
        return None

    def load_latest_autosave(self) -> Optional[dict]:
        """Load the most recent auto-save file.

        Returns:
            State dictionary, or None if no auto-save exists
        """
        latest = self.get_latest_autosave()
        if not latest:
            return None

        try:
            with open(latest, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def list_autosaves(self) -> list[tuple[Path, datetime]]:
        """List all available auto-save files.

        Returns:
            List of (filepath, timestamp) tuples
        """
        autosave_files = sorted(
            self.save_dir.glob("autosave_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        result = []
        for filepath in autosave_files:
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            result.append((filepath, mtime))

        return result

    def delete_autosave(self, filepath: Path) -> bool:
        """Delete a specific auto-save file.

        Args:
            filepath: Path to auto-save file

        Returns:
            True if deletion successful
        """
        try:
            filepath.unlink()
            return True
        except OSError:
            return False

    def clear_all_autosaves(self) -> int:
        """Delete all auto-save files.

        Returns:
            Number of files deleted
        """
        count = 0
        for filepath in self.save_dir.glob("autosave_*.json"):
            try:
                filepath.unlink()
                count += 1
            except OSError:
                pass
        return count

    def set_interval(self, seconds: int) -> None:
        """Change auto-save interval.

        Args:
            seconds: New interval in seconds
        """
        self.interval = max(60, seconds)  # Minimum 1 minute

        # Restart timer with new interval if running
        if self.enabled:
            self.stop()
            self.start()

    def manual_save(self) -> bool:
        """Trigger a manual save immediately.

        Returns:
            True if save successful
        """
        if not self._save_callback:
            return False

        try:
            state = self._save_callback()
            self._save_state(state)
            self.last_save_time = time.time()
            return True
        except Exception:  # pylint: disable=broad-except
            return False
