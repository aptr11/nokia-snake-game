# AGENT.md - Development & Architecture Guide

This document provides technical guidelines and architectural context for autonomous agents and developers working on this codebase.

---

## 1. Project Philosophy

- **Zero External Dependencies**: The project relies exclusively on the Python standard library (`curses`, `wave`, `struct`, `collections`, `json`, `argparse`). Do not introduce external package requirements (e.g., Pygame, NumPy) for core runtime functionality.
- **Portability & Graceful Degradation**: The game must run across diverse terminal environments. Curses operations (like `curs_set`, `init_pair`, or `start_color`) must be wrapped in error-handling logic to avoid crashes in constrained terminals.
- **Square Grid Aspect Ratio**: Terminal characters have an approximate 1:2 width-to-height ratio. The game represents each grid block as two horizontal characters (`BLOCK_CHAR_WIDTH = 2`) to create square cells.

---

## 2. Codebase Structure

```
nokia-snake/
├── nokia_snake.py           # CLI entrypoint and argument parser
├── pyproject.toml           # Package configuration & metadata
├── README.md                # Player-facing guide
├── AGENT.md                 # Technical architecture (this file)
├── nokia_snake/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Global constants, levels, delays, color themes
│   ├── audio.py             # Synthesized square-wave audio engine
│   ├── mazes.py             # Maze obstacle definitions and wrap flags
│   ├── game.py              # Core simulation state, movement, collision detection
│   ├── bot.py               # BFS pathfinding bot for autoplay
│   ├── renderer.py          # Dual-mode curses renderer (Phone Bezel & LCD)
│   ├── menu.py              # Menu state controller and navigation
│   └── main.py              # Main event loop, resize handling, key routing
└── tests/
    └── test_game.py         # Unit test suite
```

---

## 3. Module Responsibilities

### `nokia_snake/config.py`
Defines game constants:
- `GRID_WIDTH` (20) and `GRID_HEIGHT` (10).
- Direction vectors: `DIR_UP`, `DIR_DOWN`, `DIR_LEFT`, `DIR_RIGHT`.
- `LEVEL_DELAYS`: Step intervals for skill levels 1 through 9.
- `THEMES`: Color definitions for 256-color and 8-color terminal palettes.

### `nokia_snake/game.py`
Encapsulates state and game rules:
- `snake`: Ordered list of `(x, y)` tuples, where index `0` is the head and index `-1` is the tail.
- `input_queue`: A `deque(maxlen=3)` that stores valid directional inputs. Prevents accidental reversal (180° turns into the neck) and buffers quick turns.
- `update()`: Advances simulation if the elapsed time exceeds `tick_delay`.
- Dynamic acceleration: Decreases `tick_delay` slightly as pellets are eaten.

### `nokia_snake/renderer.py`
Handles all visual presentation:
- Manages color pairs (`PAIR_LCD_NORMAL`, `PAIR_LCD_INVERSE`, etc.).
- Renders two distinct display modes:
  - `VIEW_PHONE`: Renders the ASCII/Unicode phone casing, complete with backlit keypad lighting upon directional keypresses.
  - `VIEW_LCD`: Renders an isolated LCD canvas with header status and borders.
- Safe drawing helper `safe_addstr()` prevents out-of-bounds curses writing and avoids writing to the lower-right terminal cell which triggers terminal scroll errors.

### `nokia_snake/audio.py`
Synthesizes 8-bit style square-wave audio in memory using the `wave` and `struct` modules:
- Audio buffers are submitted to an internal worker thread via a queue to ensure audio playback never blocks the curses game loop.
- Uses `aplay -q` on Linux systems; degrades gracefully to terminal bell (`\a`) or silent operation if audio devices are unavailable.

### `nokia_snake/bot.py`
Implements autonomous decision-making using Breadth-First Search (BFS):
- Calculates shortest collision-free paths to active food or bonus items.
- Falls back to open-space maximization if no direct path exists.

---

## 4. State Machine Architecture

The top-level application state in `nokia_snake/main.py` transitions as follows:

```
    [ MENU ]  <============================>  [ PLAYING ]
       │                                           │
       │                                           ▼
       │                                      [ GAME OVER ]
       │                                           │
       │ (if score is high score)                  ▼
       └──────────────────────────────────  [ NAME ENTRY ]
```

- When returning to the menu during an active game via `Q` or `Esc`, the game is paused, and `menu.has_active_game` is set to `True`, enabling the `Continue` option.

---

## 5. Development & Testing Workflow

### Running the Test Suite
Execute the test runner before committing changes:
```bash
python3 -m unittest discover -s tests -v
```

### Adding New Mazes
1. Open `nokia_snake/mazes.py`.
2. Add a new maze entry to `get_mazes()`:
   ```python
   walls: Set[Coord] = set()
   # Add obstacle tuples (x, y) where 0 <= x < 20 and 0 <= y < 10
   # Keep coordinates (3..5, 5) free for the snake starting position
   mazes["snake2_custom"] = Maze(
       name="Maze Name",
       desc="Description",
       has_wrap=True,
       walls=walls
   )
   ```
3. Add a corresponding test case in `tests/test_game.py`.

### Adding New Color Themes
1. Open `nokia_snake/config.py`.
2. Append a theme dictionary to `THEMES` specifying foreground/background 256-color indices.
3. Test in both 256-color and 8-color fallback environments.

---

## 6. Code Style & Standards

- Adhere to **PEP 8** style conventions.
- Maintain comprehensive type annotations for function signatures.
- Keep terminal coordinates clear: `(y, x)` for curses API calls, `(x, y)` for game grid coordinates.
