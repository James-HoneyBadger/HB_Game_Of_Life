# Plugin Development

LifeGrid's plugin system lets you add new automaton modes without modifying the core codebase. Drop a `.py` file in the `plugins/` directory and it will be discovered automatically at startup.

---

## Creating a Plugin

### 1. Subclass `AutomatonPlugin`

Every plugin must implement three properties and one factory method:

```python
from src.plugin_system import AutomatonPlugin
from src.automata.base import CellularAutomaton
import numpy as np
from scipy.signal import convolve2d


class MyAutomaton(CellularAutomaton):
    """Your automaton implementation."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=int)

    def step(self) -> None:
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]])
        neighbors = convolve2d(
            (self.grid > 0).astype(int), kernel,
            mode='same', boundary='wrap'
        )
        # Apply your rules here
        new_grid = np.zeros_like(self.grid)
        birth = (self.grid == 0) & np.isin(neighbors, [3, 6, 7, 8])
        survive = (self.grid > 0) & np.isin(neighbors, [3, 4, 6, 7, 8])
        new_grid[birth] = 1
        new_grid[survive] = self.grid[survive]
        self.grid = new_grid

    def get_grid(self) -> np.ndarray:
        return self.grid

    def set_cell(self, x: int, y: int, value: int = 1) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = value

    def reset(self) -> None:
        self.grid = np.zeros((self.height, self.width), dtype=int)


class MyPlugin(AutomatonPlugin):
    @property
    def name(self) -> str:
        return "My Custom Rule"

    @property
    def description(self) -> str:
        return "B368/S3468 — an example custom automaton"

    @property
    def version(self) -> str:
        return "1.0"

    def create_automaton(self, width: int, height: int) -> CellularAutomaton:
        return MyAutomaton(width, height)
```

### 2. Save the file

Save your plugin as `plugins/my_custom_rule.py`. The filename doesn't matter — LifeGrid scans all `.py` files in the directory.

### 3. Restart LifeGrid

The new mode appears in the mode selector automatically.

---

## Plugin API

### `AutomatonPlugin` (abstract base class)

| Member | Type | Description |
|--------|------|-------------|
| `name` | property → str | Display name shown in the mode selector |
| `description` | property → str | Short description of the rule |
| `version` | property → str | Plugin version string |
| `create_automaton(width, height)` | method → CellularAutomaton | Factory that returns a configured automaton instance |

### `CellularAutomaton` (abstract base class)

Your automaton must implement:

| Method | Signature | Description |
|--------|-----------|-------------|
| `step` | `() -> None` | Advance one generation |
| `get_grid` | `() -> np.ndarray` | Return the current grid as a 2D numpy array |
| `set_cell` | `(x, y, value) -> None` | Set a single cell's state |
| `reset` | `() -> None` | Clear the grid to all zeros |

The grid should be a 2D integer array of shape `(height, width)` where `0` means dead and positive integers represent live/colored states.

---

## Example: Day & Night Plugin

The included `plugins/day_and_night.py` implements B3678/S34678:

```python
from src.plugin_system import AutomatonPlugin
from src.automata.lifelike import LifeLikeAutomaton
from src.automata.base import CellularAutomaton


class DayAndNightPlugin(AutomatonPlugin):
    @property
    def name(self) -> str:
        return "Day & Night"

    @property
    def description(self) -> str:
        return "B3678/S34678 — symmetric behavior for ON and OFF cells"

    @property
    def version(self) -> str:
        return "1.0"

    def create_automaton(self, width: int, height: int) -> CellularAutomaton:
        return LifeLikeAutomaton(width, height, birth={3, 6, 7, 8}, survival={3, 4, 6, 7, 8})
```

This plugin reuses `LifeLikeAutomaton` for the step logic, so only the plugin metadata and B/S parameters need to be defined.

---

## Tips

- **Reuse `LifeLikeAutomaton`** for any totalistic Life-like rule — just supply birth and survival sets.
- **Multi-state automata** can use integers > 1 in the grid. The GUI renders states 0–3 with distinct colors.
- **Test your plugin** by instantiating it directly:
  ```python
  plugin = MyPlugin()
  auto = plugin.create_automaton(50, 50)
  auto.set_cell(25, 25, 1)
  auto.step()
  print(auto.get_grid().sum())
  ```
- Plugins are loaded via `PluginManager.load_plugins_from_directory()`. If a plugin fails to load (import error, missing methods), it is skipped with a warning — it won't crash the application.
