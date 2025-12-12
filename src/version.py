"""LifeGrid version info.

Tries to derive version from Git tags; falls back to static.
"""

from __future__ import annotations

import subprocess


def _git_version() -> str | None:
	"""Return version string from `git describe --tags --always`, if available."""
	try:
		out = subprocess.check_output(
			["git", "describe", "--tags", "--always"],
			stderr=subprocess.DEVNULL,
		)
		return out.decode("utf-8").strip()
	except Exception:
		return None


__version__ = _git_version() or "1.0.0"

