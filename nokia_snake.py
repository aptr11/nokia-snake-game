#!/usr/bin/env python3
"""
Nokia Snake: Terminal emulation of the legendary game launched by Nokia in 1997.
Created by Taneli Armanto for the Nokia 6110.

Usage:
    ./nokia_snake.py [options]

Options:
    -l, --level LEVEL     Starting skill level (1-9) [default: 5]
    -m, --mode MODE       Game mode: 'classic' (1997) or 'snake2' (2000) [default: classic]
    -t, --theme THEME     Color theme: 'classic_green', 'monochrome', 'matrix', 'amber'
    --lcd                 Launch directly in Fullscreen LCD mode (no phone frame)
    --no-sound            Launch with buzzer audio muted
    -h, --help            Show this help message
    -v, --version         Show game version
"""

import argparse
import os
import sys

# Ensure module path is loaded
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from nokia_snake.config import VERSION, THEMES, MODE_SNAKE1, MODE_SNAKE2, VIEW_PHONE, VIEW_LCD
from nokia_snake.main import NokiaSnakeApp
import curses

def parse_args():
    parser = argparse.ArgumentParser(
        description="Nokia Snake: Terminal emulation of the legendary 1997 Nokia game.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Key Controls:
  2 / Up / W     Move Up
  8 / Down / S   Move Down
  4 / Left / A   Move Left
  6 / Right / D  Move Right
  P / Space      Pause / Resume
  M              Mute / Unmute buzzer sound
  V              Toggle Phone Bezel / Full LCD view
  T              Cycle LCD color themes
  Q / Esc        Return to Menu / Quit

Authentic Nokia Keypad:
  Keys 2, 4, 6, 8 work exactly like the original Nokia phone keypad!
"""
    )
    parser.add_argument("-l", "--level", type=int, choices=range(1, 10), default=5,
                        help="Starting skill level (1-9)")
    parser.add_argument("-m", "--mode", choices=["classic", "snake2"], default="classic",
                        help="Game mode: 'classic' (Nokia 6110) or 'snake2' (Nokia 3310)")
    parser.add_argument("-t", "--theme", choices=list(THEMES.keys()), default="classic_green",
                        help="LCD Color Theme")
    parser.add_argument("--lcd", action="store_true",
                        help="Start in Full Retro LCD mode without phone bezel")
    parser.add_argument("--no-sound", action="store_true",
                        help="Disable buzzer audio")
    parser.add_argument("--demo", action="store_true",
                        help="Launch in autoplay demo mode (snake plays itself using AI)")
    parser.add_argument("-v", "--version", action="version", version=f"Nokia Snake {VERSION}")
    return parser.parse_args()

def main():
    args = parse_args()

    # Ensure TERM is set properly if launched in bare terminal
    if os.environ.get("TERM") in (None, "", "dumb"):
        os.environ["TERM"] = "xterm-256color"

    def curses_runner(stdscr):
        app = NokiaSnakeApp(stdscr)

        # Apply CLI overrides
        if args.level:
            app.game.set_level(args.level)
        if args.mode:
            app.game.set_mode(MODE_SNAKE1 if args.mode == "classic" else MODE_SNAKE2)
        if args.theme:
            app.renderer.set_theme(args.theme)
        if args.lcd:
            app.renderer.view_mode = VIEW_LCD
        if args.no_sound:
            app.sound.enabled = False
        if args.demo:
            app.demo_mode = True
            app.app_state = "playing"
            app.menu.has_active_game = True

        app.run()

    try:
        curses.wrapper(curses_runner)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # If terminal was too small or unexpected curses error
        print(f"\nGame exited: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
