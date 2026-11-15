"""
Nokia Menu Controller and Sub-screens.
Implements the authentic Nokia phone menu system.
"""

import curses
import time
from typing import List, Tuple, Dict, Any, Optional

from .config import (
    THEMES, VIEW_PHONE, VIEW_LCD, MODE_SNAKE1, MODE_SNAKE2
)
from .game import SnakeGame
from .highscores import HighScoreManager
from .renderer import Renderer
from .audio import SoundEngine

# Menu state IDs
STATE_MAIN_MENU = "main_menu"
STATE_LEVEL_SELECT = "level_select"
STATE_MODE_SELECT = "mode_select"
STATE_MAZE_SELECT = "maze_select"
STATE_HIGHSCORES = "highscores"
STATE_SETTINGS = "settings"
STATE_HELP = "help"

class MenuController:
    def __init__(self, game: SnakeGame, renderer: Renderer, highscores: HighScoreManager, sound: SoundEngine):
        self.game = game
        self.renderer = renderer
        self.highscores = highscores
        self.sound = sound

        self.current_state = STATE_MAIN_MENU
        self.selected_index = 0
        self.has_active_game = False

    def get_main_menu_items(self) -> List[Tuple[str, str]]:
        """Returns list of (label, action_id)."""
        items = []
        if self.has_active_game and not self.game.is_game_over:
            items.append(("1. Continue", "continue"))

        items.append(("New Game", "new_game"))
        items.append((f"Skill Level: < {self.game.level} >", "level"))
        
        mode_label = "Snake 1997" if self.game.game_mode == MODE_SNAKE1 else "Snake II"
        items.append((f"Game Mode: < {mode_label} >", "mode"))

        if self.game.game_mode == MODE_SNAKE2:
            items.append((f"Maze: < {self.game.maze.name} >", "maze"))

        items.append(("High Scores", "highscores"))

        view_label = "Phone" if self.renderer.view_mode == VIEW_PHONE else "Full LCD"
        items.append((f"View: < {view_label} >", "view"))

        theme_label = THEMES[self.renderer.theme_name]["name"].split()[0]
        items.append((f"Theme: < {theme_label} >", "theme"))

        sound_label = "ON" if self.sound.enabled else "OFF"
        items.append((f"Sound: < {sound_label} >", "sound"))

        items.append(("Instructions", "help"))
        items.append(("Exit", "exit"))
        return items

    def handle_input(self, key: int) -> Optional[str]:
        """
        Handle a menu key event.
        Returns:
            "start_game": start a fresh game
            "resume_game": resume paused game
            "quit": exit application
            None: remain in menu
        """
        if self.current_state == STATE_MAIN_MENU:
            return self._handle_main_menu(key)
        elif self.current_state == STATE_HIGHSCORES:
            return self._handle_highscores_view(key)
        elif self.current_state == STATE_HELP:
            return self._handle_help_view(key)
        return None

    def _handle_main_menu(self, key: int) -> Optional[str]:
        items = self.get_main_menu_items()
        num_items = len(items)

        # Navigation UP
        if key in (curses.KEY_UP, ord('k'), ord('K'), ord('w'), ord('W'), ord('2')):
            self.sound.play_click()
            self.renderer.highlight_key("UP")
            self.selected_index = (self.selected_index - 1) % num_items
            return None

        # Navigation DOWN
        if key in (curses.KEY_DOWN, ord('j'), ord('J'), ord('s'), ord('S'), ord('8')):
            self.sound.play_click()
            self.renderer.highlight_key("DOWN")
            self.selected_index = (self.selected_index + 1) % num_items
            return None

        current_label, action = items[self.selected_index]

        # Navigation LEFT (adjust option)
        if key in (curses.KEY_LEFT, ord('a'), ord('A'), ord('4')):
            self.sound.play_click()
            self.renderer.highlight_key("LEFT")
            if action == "level":
                self.game.set_level(self.game.level - 1 if self.game.level > 1 else 9)
            elif action == "mode":
                new_m = MODE_SNAKE2 if self.game.game_mode == MODE_SNAKE1 else MODE_SNAKE1
                self.game.set_mode(new_m)
            elif action == "maze":
                self._cycle_maze(-1)
            elif action == "view":
                self.renderer.toggle_view()
            elif action == "theme":
                self._cycle_theme(-1)
            elif action == "sound":
                self.sound.toggle()
            return None

        # Navigation RIGHT (adjust option)
        if key in (curses.KEY_RIGHT, ord('d'), ord('D'), ord('6')):
            self.sound.play_click()
            self.renderer.highlight_key("RIGHT")
            if action == "level":
                self.game.set_level(self.game.level + 1 if self.game.level < 9 else 1)
            elif action == "mode":
                new_m = MODE_SNAKE2 if self.game.game_mode == MODE_SNAKE1 else MODE_SNAKE1
                self.game.set_mode(new_m)
            elif action == "maze":
                self._cycle_maze(1)
            elif action == "view":
                self.renderer.toggle_view()
            elif action == "theme":
                self._cycle_theme(1)
            elif action == "sound":
                self.sound.toggle()
            return None

        # Selection (Enter, Space, 5, Navi-key)
        if key in (10, 13, curses.KEY_ENTER, ord(' '), ord('5')):
            self.sound.play_click()
            self.renderer.highlight_key("NAVI")
            if action == "continue":
                self.game.is_paused = False
                return "resume_game"
            elif action == "new_game":
                self.game.reset()
                self.has_active_game = True
                return "start_game"
            elif action == "level":
                # Quick cycle level
                self.game.set_level(self.game.level + 1 if self.game.level < 9 else 1)
            elif action == "mode":
                new_m = MODE_SNAKE2 if self.game.game_mode == MODE_SNAKE1 else MODE_SNAKE1
                self.game.set_mode(new_m)
            elif action == "maze":
                self._cycle_maze(1)
            elif action == "highscores":
                self.current_state = STATE_HIGHSCORES
            elif action == "view":
                self.renderer.toggle_view()
            elif action == "theme":
                self.renderer.cycle_theme()
            elif action == "sound":
                self.sound.toggle()
            elif action == "help":
                self.current_state = STATE_HELP
            elif action == "exit":
                return "quit"
            return None

        # Shortcut keys directly from menu
        if key in (ord('v'), ord('V')):
            self.renderer.toggle_view()
        elif key in (ord('t'), ord('T')):
            self.renderer.cycle_theme()
        elif key in (ord('m'), ord('M')):
            self.sound.toggle()
        elif key in (ord('q'), ord('Q'), 27):  # 27 = Esc
            return "quit"

        return None

    def _cycle_maze(self, delta: int):
        maze_keys = [k for k in self.game.mazes.keys() if k.startswith("snake2")]
        if not maze_keys:
            return
        current_idx = maze_keys.index(self.game.maze_id) if self.game.maze_id in maze_keys else 0
        new_idx = (current_idx + delta) % len(maze_keys)
        self.game.set_maze(maze_keys[new_idx])

    def _cycle_theme(self, delta: int):
        keys = list(THEMES.keys())
        idx = (keys.index(self.renderer.theme_name) + delta) % len(keys)
        self.renderer.set_theme(keys[idx])

    def _handle_highscores_view(self, key: int) -> Optional[str]:
        # Any key returns to main menu
        if key != -1:
            self.sound.play_click()
            self.current_state = STATE_MAIN_MENU
        return None

    def _handle_help_view(self, key: int) -> Optional[str]:
        if key != -1:
            self.sound.play_click()
            self.current_state = STATE_MAIN_MENU
        return None

    def render(self):
        if self.current_state == STATE_MAIN_MENU:
            items = [item[0] for item in self.get_main_menu_items()]
            self.renderer.render_menu("S N A K E", items, self.selected_index)
        elif self.current_state == STATE_HIGHSCORES:
            self._render_highscores_screen()
        elif self.current_state == STATE_HELP:
            self._render_help_screen()

    def _render_highscores_screen(self):
        top_scores = self.highscores.get_top(7)
        lines = []
        if not top_scores:
            lines.append("No High Scores Yet!")
        else:
            for i, s in enumerate(top_scores, start=1):
                name = s.get("name", "---")[:4]
                score = s.get("score", 0)
                lvl = s.get("level", 1)
                lines.append(f"{i}. {name:<4}  {score:04d}  L{lvl}")

        self.renderer.render_menu("HIGH SCORES", lines, 0, "[Press Any Key for Menu]")

    def _render_help_screen(self):
        lines = [
            "NOKIA 6110 SNAKE (1997)",
            "Original by Taneli Armanto",
            "-------------------------",
            "Controls:",
            "  2 / Up   : Move Up",
            "  8 / Down : Move Down",
            "  4 / Left : Move Left",
            "  6 / Right: Move Right",
            "  WASD & Arrows supported",
            "  P: Pause  M: Sound",
            "  V: Switch Phone/LCD View",
            "  Q: Return to Menu",
        ]
        self.renderer.render_menu("INSTRUCTIONS", lines, 0, "[Press Any Key for Menu]")
