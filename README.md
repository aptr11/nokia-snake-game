# 🐍 Nokia Snake (1997 Terminal Emulation)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#requirements)

```
                   .----------------------------------------.
                  /                  NOKIA                   \
                 |                  [||||]                    |
                .-+------------------------------------------+-.
                | |ıll 0042       HI: 0500        L5 [■■■■]| |
                | |----------------------------------------| |
                | |                                        | |
                | |                  ◆                     | |
                | |                                        | |
                | |      ████►█                            | |
                | |                                        | |
                | |                                        | |
                .-+------------------------------------------+-.
                 |             (--- NAVI KEY ---)             |
                 |          [ 1 ]    [ 2▲]    [ 3 ]           |
                 |          [ 4◄]    [ 5 ]    [ 6►]           |
                 |          [ 7 ]    [ 8▼]    [ 9 ]           |
                 |          [ * ]    [ 0_]    [ # ]           |
                  \__________________________________________/
              [Q] Menu  [P] Pause  [M] Sound  [V] View  [T] Theme
```

An authentic terminal recreation of the original **Snake** mobile game created in 1997 by Nokia engineer **Taneli Armanto** for the **Nokia 6110**, and expanded on the **Nokia 3310**.

Built entirely in Python using standard library modules (`curses`, `wave`, `struct`, `collections`), requiring **zero third-party dependencies**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [How to Run](#-how-to-run)
- [How to Play](#-how-to-play)
  - [Game Modes](#game-modes)
  - [Controls Reference](#controls-reference)
  - [Display Modes & Themes](#display-modes--themes)
  - [Scoring & Mechanics](#scoring--mechanics)
- [Running Tests](#-running-tests)
- [Project Architecture](#-project-architecture)
- [History & Credits](#-history--credits)

---

## ✨ Features

- **Iconic Phone Bezel Mode**: Full Nokia 3310 phone chassis with curved housing, speaker slit, Navi-key, and a **backlit keypad that illuminates in real-time** when you press directional keys.
- **Fullscreen Retro LCD Mode**: Pure, distraction-free monochrome LCD screen with Nokia battery indicator `[■■■■]`, signal strength `ıll`, level, and score.
- **Two Historical Game Modes**:
  - **Snake 1997 (Nokia 6110)**: Solid outer boundary walls, classic single-dot growth, strict original collision rules.
  - **Snake II (Nokia 3310)**: Screen edge wraparound, 5 distinct mazes (*Tunnel*, *Fortresses*, *Double Rails*, *Labyrinth*), and timed bonus insects with countdown timer bars.
- **Authentic Monophonic Sound Engine**:
  - Real-time synthesized square waves matching the exact frequency and timbre of classic Nokia piezoelectric buzzers.
  - Includes opening **Nokia Ringtone** melody, eating blip (1046 Hz), bonus double chirps, crash buzzes, and high-score fanfares.
  - Non-blocking daemon playback via ALSA `aplay` with automatic fallback to terminal bell (`\a`).
- **4 Retro Color Themes**:
  - *Nokia 3310 Green* (Classic `#9BBC0F` olive backlight)
  - *Nokia 3210 Silver/Grey* (Crisp monochrome LCD)
  - *Nokia 8110 Neo Matrix* (High-contrast phosphor green on jet black)
  - *Amber Retro 90s* (Warm gold calculator/pager display)
- **High-Responsiveness Input Buffer**: Queues rapid succession turns (FIFO) to prevent suicide on tight corners. Immediate 180° turn into self is rejected.
- **Persistent High Scores**: Local storage in `~/.config/nokia_snake/highscores.json` with player initials entry.
- **AI Autoplay Demo Mode**: Built-in BFS pathfinding bot that plays the game autonomously (`--demo`).

---

## 💻 Requirements

- **Python 3.8+**
- Any standard terminal emulator supporting ANSI / 256 colors (e.g. `gnome-terminal`, `xterm`, `kitty`, `alacritty`, `iTerm2`, Windows Terminal / WSL).
- Terminal window size of at least **60 columns × 24 rows** (recommended: 80×24 or higher).
- *(Optional)* ALSA `aplay` utility on Linux for hardware audio playback (standard on Ubuntu, Debian, Fedora, Arch). Automatically falls back to terminal bell if unavailable.

---

## 🚀 Installation

### Option 1: Standalone / Quick Link (Recommended)

Clone the repository and run directly:

```bash
git clone https://github.com/YOUR_USERNAME/nokia-snake.git
cd nokia-snake

# Make executable and symlink to user's bin directory:
chmod +x nokia_snake.py
mkdir -p ~/.local/bin
ln -sf "$(pwd)/nokia_snake.py" ~/.local/bin/nokia-snake
```

Now you can run `nokia-snake` from any directory!

### Option 2: Pip Local Editable Install

```bash
git clone https://github.com/YOUR_USERNAME/nokia-snake.git
cd nokia-snake
pip install -e .
```

This installs the `nokia-snake` console entrypoint directly into your active Python environment.

---

## 🕹️ How to Run

### Basic Usage

```bash
# Launch the game with default settings (Nokia 3310 phone bezel, Level 5, Classic 1997 mode)
nokia-snake
```

Or execute directly with Python:

```bash
python3 nokia_snake.py
```

### Command-Line Flags

```text
usage: nokia_snake.py [-h] [-l {1,2,3,4,5,6,7,8,9}] [-m {classic,snake2}]
                      [-t {classic_green,monochrome,matrix,amber}] [--lcd]
                      [--no-sound] [--demo] [-v]

options:
  -h, --help            Show this help message and exit
  -l, --level LEVEL     Starting skill level (1-9, default: 5)
  -m, --mode MODE       Game mode: 'classic' (1997) or 'snake2' (2000)
  -t, --theme THEME     LCD theme: 'classic_green', 'monochrome', 'matrix', 'amber'
  --lcd                 Launch directly in Fullscreen LCD mode (no phone frame)
  --no-sound            Disable buzzer sound
  --demo                Launch in autoplay demo mode (AI bot plays automatically)
  -v, --version         Show game version
```

### Examples

```bash
# Play on max difficulty (Level 9) with classic solid walls:
nokia-snake -l 9 -m classic

# Play Snake II with mazes and edge wraparound:
nokia-snake -m snake2

# Fullscreen LCD mode in Matrix Phosphor theme:
nokia-snake --lcd -t matrix

# Watch the AI bot play itself:
nokia-snake --demo
```

---

## 🎮 How to Play

### Game Modes

1. **Snake 1997 (Nokia 6110)**:
   - The snake moves continuously inside a solid rectangular boundary.
   - Hitting any wall or hitting your own tail results in an instant crash.
   - Food pellets appear one at a time.
2. **Snake II (Nokia 3310)**:
   - Supports 5 distinct maze configurations: *Open Wrap*, *Tunnel*, *Fortresses*, *Double Rails*, and *Labyrinth*.
   - When no wall blocks the screen perimeter, the snake **wraps around** to the opposite edge.
   - After every 5 pellets eaten, a **bonus insect** appears with a countdown bar. Consuming it quickly awards major bonus points!

### Controls Reference

| Action | Nokia Numpad | Arrow Keys | WASD | Vim Keys |
| :--- | :---: | :---: | :---: | :---: |
| **Move Up** | `2` | `↑` | `W` | `K` |
| **Move Down** | `8` | `↓` | `S` | `J` |
| **Move Left** | `4` | `←` | `A` | `H` |
| **Move Right** | `6` | `→` | `D` | `L` |
| **Select / Confirm** | `5` / Navi-key | `Enter` | `Space` | - |
| **Pause / Resume** | - | `Space` | `P` | `P` |
| **Toggle Phone / LCD View** | - | `V` | `V` | `V` |
| **Cycle Theme** | - | `T` | `T` | `T` |
| **Mute / Unmute Audio** | - | `M` | `M` | `M` |
| **Menu / Back / Quit** | `C` | `Esc` | `Q` | `Q` |

### Display Modes & Themes

- **Toggle View (`V`)**: Press `V` at any time (even during active gameplay) to switch seamlessly between **Phone Bezel Mode** (with glowing keypad buttons) and **Fullscreen LCD Mode**.
- **Cycle Theme (`T`)**: Press `T` during gameplay or select via the menu to toggle among the 4 color palettes:
  - *Classic 3310 Green*
  - *Silver Monochrome 3210*
  - *Matrix CRT Green*
  - *Amber Retro 90s*

### Scoring & Mechanics

- **Initial Length**: Starts at 3 segments.
- **Regular Pellet**: Increases length by 1 segment. Score awarded = `Current Skill Level` (e.g. eating food at Level 5 awards 5 points; at Level 9 awards 9 points).
- **Dynamic Speedup**: In addition to starting level speeds, the snake subtly accelerates dynamically by 1.2ms per food eaten, faithfully mimicking Taneli Armanto's speed curve.
- **Bonus Insects (Snake II)**: Award `(time_remaining / total_time) * Level * 10 + (Level * 5)` points.

---

## 🧪 Running Tests

The test suite covers game physics, direction buffering, collision detection, wraparound geometry, audio wave generation, and high-score persistence:

```bash
python3 -m unittest discover -s tests -v
```

All 10 test suites run in under 0.05 seconds with zero external dependencies.

---

## 📂 Project Architecture

```
nokia-snake/
├── nokia_snake.py           # CLI entrypoint script
├── pyproject.toml           # Modern package configuration
├── README.md                # Player guide & documentation
├── AGENT.md                 # Technical architecture & development guide
├── nokia_snake/
│   ├── __init__.py          # Package initialization & version
│   ├── config.py            # Grid dimensions, speed levels, themes & colors
│   ├── audio.py             # Nokia square-wave synthesizer & background worker
│   ├── mazes.py             # Snake I solid borders & Snake II mazes (1-5)
│   ├── game.py              # Core physics, input queue, scoring & state
│   ├── bot.py               # BFS pathfinding autonomous autoplay bot
│   ├── renderer.py          # Curses display engine (Phone bezel + LCD modes)
│   ├── menu.py              # Nokia hierarchical menu navigation & sub-screens
│   └── main.py              # Application loop, resize handling & event bus
└── tests/
    └── test_game.py         # Automated unit test suite
```

---

## 🏛️ History & Credits

In late 1997, Nokia engineer **Taneli Armanto** was tasked with creating simple games for the upcoming **Nokia 6110**. Constrained by mere kilobytes of memory and the phone's 84×48 pixel monochrome LCD, Armanto crafted an elegant adaptation of the arcade classic *Blockade* (1976).

Controlled using the phone's physical numeric keypad (`2`, `4`, `6`, `8`), the game became an overnight international sensation, shipping on over 400 million handsets worldwide and establishing mobile gaming as an everyday cultural phenomenon.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
