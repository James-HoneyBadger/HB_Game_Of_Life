"""Public LifeGrid 4 package namespace."""

from __future__ import annotations

import importlib
import sys

from version import __version__

# The implementation modules remain in their established locations during the
# migration. Expose them through the stable v4 namespace immediately.
_TOP_LEVEL_MODULES = ("core", "automata", "advanced", "performance", "api", "gui")
_VERSION_4_MODULES = ("io", "plugins", "boundaries", "patterns", "scenarios")
_APP_SUBMODULE_ALIASES = {
    "autosave_manager": "autosave_manager",
    "config_manager": "config_manager",
    "export_manager": "export_manager",
}
_CORE_SUBMODULE_ALIASES = {
    "boundary": "core.boundary",
    "config": "core.config",
    "simulator": "core.simulator",
    "snapshot": "core.snapshot",
    "undo_manager": "core.undo_manager",
    "version": "version",
}

for _name in _TOP_LEVEL_MODULES:
    try:
        _module = importlib.import_module(_name)
    except ImportError:
        # Optional subsystems remain importable when their dependencies exist.
        continue
    sys.modules[f"{__name__}.{_name}"] = _module
    setattr(sys.modules[__name__], _name, _module)

for _name in _VERSION_4_MODULES:
    try:
        _module = importlib.import_module(f"{__name__}.{_name}")
    except ImportError:
        # Fallback to legacy top-level import names when the V4 module is absent.
        try:
            _module = importlib.import_module(_name)
        except ImportError:
            continue
    sys.modules[f"{__name__}.{_name}"] = _module
    setattr(sys.modules[__name__], _name, _module)

for _name, _target in _APP_SUBMODULE_ALIASES.items():
    try:
        _module = importlib.import_module(_target)
    except ImportError:
        continue
    sys.modules[f"{__name__}.{_name}"] = _module
    setattr(sys.modules[__name__], _name, _module)

for _name, _target in _CORE_SUBMODULE_ALIASES.items():
    try:
        _module = importlib.import_module(_target)
    except ImportError:
        continue
    sys.modules[f"{__name__}.{_name}"] = _module
    setattr(sys.modules[__name__], _name, _module)

try:
    from core import (
        BoundaryMode,
        Simulator,
        SimulatorConfig,
        convolve_with_boundary,
        list_boundary_modes,
        roll_with_boundary,
    )
    for _symbol in (
        "BoundaryMode",
        "Simulator",
        "SimulatorConfig",
        "convolve_with_boundary",
        "list_boundary_modes",
        "roll_with_boundary",
    ):
        setattr(sys.modules[__name__], _symbol, globals()[_symbol])
except ImportError:
    pass

try:
    from automata import ConwayGameOfLife
    setattr(sys.modules[__name__], "ConwayGameOfLife", ConwayGameOfLife)
except ImportError:
    pass

try:
    from scenarios import build_scenario, get_scenario_names
    for _symbol in ("build_scenario", "get_scenario_names"):
        setattr(sys.modules[__name__], _symbol, globals()[_symbol])
except ImportError:
    pass

try:
    from patterns import get_pattern_description, get_pattern_coords
    for _symbol in ("get_pattern_description", "get_pattern_coords"):
        setattr(sys.modules[__name__], _symbol, globals()[_symbol])
except ImportError:
    pass

__all__ = [
    "__version__",
    *[
        name
        for name in (
            *_TOP_LEVEL_MODULES,
            *_VERSION_4_MODULES,
            "BoundaryMode",
            "Simulator",
            "SimulatorConfig",
            "convolve_with_boundary",
            "list_boundary_modes",
            "roll_with_boundary",
            "ConwayGameOfLife",
            "build_scenario",
            "get_scenario_names",
            "get_pattern_description",
            "get_pattern_coords",
        )
        if hasattr(sys.modules[__name__], name)
    ],
]
