"""
Main entry point and event loop for Nokia Snake.
"""

import curses
import os
import signal
import sys
import time

from .config import (
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    VIEW_PHONE, VIEW_LCD, MODE_BLOCKADE,
    BLOCKADE_OPPONENT_CPU, BLOCKADE_OPPONENT_HUMAN
)
from .audio import SoundEngine
from .game import SnakeGame
from .highscores import HighScoreManager
from .renderer import Renderer
from .menu import MenuController
from .bot import SnakeBot

# Top-level application states
APP_STATE_MENU = "menu"
APP_STATE_PLAYING = "playing"
APP_STATE_GAME_OVER = "game_over"
APP_STATE_NAME_ENTRY = "name_entry"

class NokiaSnakeApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        # Initialize audio engine
        self.sound = SoundEngine(enabled=True)

        # Initialize high scores
        self.highscores = HighScoreManager()

        # Initialize game engine
        self.game = SnakeGame(self.sound)

        # Initialize renderer
        self.renderer = Renderer(self.stdscr)

        # Initialize menu
        self.menu = MenuController(self.game, self.renderer, self.highscores, self.sound)

        # Application state
        self.app_state = APP_STATE_MENU
        self.running = True
        self.demo_mode = False
        self.bot = SnakeBot(self.game)

        # High score input buffer
        self.name_buffer = ""
        self.new_score_rank = 0

        # Non-blocking input loop (timeout 25ms = ~40 FPS refresh)
        self.stdscr.timeout(25)

        # Play Nokia opening jingle on startup
        self.sound.play_nokia_tune()

    def run(self):
        while self.running:
            try:
                key = self.stdscr.getch()
            except curses.error:
                key = -1

            # Handle terminal resize
            if key == curses.KEY_RESIZE:
                self.stdscr.clear()
                continue

            if self.app_state == APP_STATE_MENU:
                self._update_menu(key)
            elif self.app_state == APP_STATE_PLAYING:
                self._update_playing(key)
            elif self.app_state == APP_STATE_GAME_OVER:
                self._update_game_over(key)
            elif self.app_state == APP_STATE_NAME_ENTRY:
                self._update_name_entry(key)

        self.sound.shutdown()

    # -------------------------------------------------------------
    # Menu State
    # -------------------------------------------------------------

    def _update_menu(self, key: int):
        action = self.menu.handle_input(key)
        if action == "start_game":
            self.app_state = APP_STATE_PLAYING
            self.menu.has_active_game = True
        elif action == "resume_game":
            self.app_state = APP_STATE_PLAYING
        elif action == "quit":
            self.running = False
            return

        self.menu.render()

    # -------------------------------------------------------------
    # Playing State
    # -------------------------------------------------------------

    def _update_playing(self, key: int):
        is_blockade = (self.game.game_mode == MODE_BLOCKADE)
        is_blockade_cpu = is_blockade and (self.game.blockade_opponent == BLOCKADE_OPPONENT_CPU)
        is_blockade_2p = is_blockade and (self.game.blockade_opponent == BLOCKADE_OPPONENT_HUMAN)

        # In-game Hotkeys
        if key in (ord('p'), ord('P'), ord(' ')):
            self.game.toggle_pause()
            self.sound.play_click()
            return
        elif key in (ord('m'), ord('M')):
            self.sound.toggle()
            return
        elif key in (ord('v'), ord('V')):
            self.renderer.toggle_view()
            return
        elif key in (ord('t'), ord('T')):
            self.renderer.cycle_theme()
            return
        elif key in (ord('q'), ord('Q'), 27):  # 27 = Esc
            # Pause and return to menu
            self.game.is_paused = True
            self.app_state = APP_STATE_MENU
            self.menu.has_active_game = True
            self.menu.selected_index = 0
            return

        # Autoplay / CPU logic
        if not self.game.is_paused and not self.game.is_round_over:
            if self.demo_mode and not is_blockade:
                bot_dir = self.bot.get_next_direction()
                if bot_dir:
                    self.game.queue_direction(bot_dir)
            elif is_blockade_cpu:
                bot_p2 = self.bot.get_next_direction_p2()
                if bot_p2:
                    self.game.queue_direction_p2(bot_p2)

        # Directional controls
        if is_blockade_2p:
            # Player 1 controls (WASD / 2,4,6,8)
            if key in (ord('w'), ord('W'), ord('2')):
                self.game.queue_direction(DIR_UP)
                self.renderer.highlight_key("UP")
            elif key in (ord('s'), ord('S'), ord('8')):
                self.game.queue_direction(DIR_DOWN)
                self.renderer.highlight_key("DOWN")
            elif key in (ord('a'), ord('A'), ord('4')):
                self.game.queue_direction(DIR_LEFT)
                self.renderer.highlight_key("LEFT")
            elif key in (ord('d'), ord('D'), ord('6')):
                self.game.queue_direction(DIR_RIGHT)
                self.renderer.highlight_key("RIGHT")

            # Player 2 controls (Arrow keys / IJKL)
            elif key in (curses.KEY_UP, ord('i'), ord('I')):
                self.game.queue_direction_p2(DIR_UP)
            elif key in (curses.KEY_DOWN, ord('k'), ord('K')):
                self.game.queue_direction_p2(DIR_DOWN)
            elif key in (curses.KEY_LEFT, ord('j'), ord('J')):
                self.game.queue_direction_p2(DIR_LEFT)
            elif key in (curses.KEY_RIGHT, ord('l'), ord('L')):
                self.game.queue_direction_p2(DIR_RIGHT)
        else:
            # Single player (Snake or Blockade vs CPU)
            if key in (curses.KEY_UP, ord('2'), ord('w'), ord('W'), ord('k'), ord('K')):
                self.demo_mode = False  # Player takes over
                self.game.queue_direction(DIR_UP)
                self.renderer.highlight_key("UP")
            elif key in (curses.KEY_DOWN, ord('8'), ord('s'), ord('S'), ord('j'), ord('J')):
                self.demo_mode = False
                self.game.queue_direction(DIR_DOWN)
                self.renderer.highlight_key("DOWN")
            elif key in (curses.KEY_LEFT, ord('4'), ord('a'), ord('A'), ord('h'), ord('H')):
                self.demo_mode = False
                self.game.queue_direction(DIR_LEFT)
                self.renderer.highlight_key("LEFT")
            elif key in (curses.KEY_RIGHT, ord('6'), ord('d'), ord('D'), ord('l'), ord('L')):
                self.demo_mode = False
                self.game.queue_direction(DIR_RIGHT)
                self.renderer.highlight_key("RIGHT")

        # Advance game logic step
        self.game.update()

        # Check for Game Over condition
        if self.game.is_game_over:
            self.renderer.flash_crash()
            self.app_state = APP_STATE_GAME_OVER
            self.menu.has_active_game = False
            return

        # Render active board
        highest = self.highscores.get_highest_score()
        self.renderer.render_game(self.game, highest)

    # -------------------------------------------------------------
    # Game Over State
    # -------------------------------------------------------------

    def _update_game_over(self, key: int):
        highest = self.highscores.get_highest_score()
        is_new_record = (self.game.score > highest and self.game.score > 0 and self.game.game_mode != MODE_BLOCKADE)

        # Wait for keypress
        if key != -1:
            self.sound.play_click()
            if self.game.game_mode != MODE_BLOCKADE and self.highscores.is_high_score(self.game.score):
                self.sound.play_highscore()
                self.app_state = APP_STATE_NAME_ENTRY
                self.name_buffer = ""
            else:
                self.app_state = APP_STATE_MENU
            return

        self.renderer.render_game(self.game, highest)
        self.renderer.render_game_over(self.game, highest, is_new_record)

    # -------------------------------------------------------------
    # High Score Initials Entry State
    # -------------------------------------------------------------

    def _update_name_entry(self, key: int):
        if key in (10, 13, curses.KEY_ENTER):
            # Save score
            entered_name = self.name_buffer.strip().upper() or "YOU"
            mode_name = "Classic 1997" if self.game.game_mode == "snake1" else "Snake II"
            self.new_score_rank = self.highscores.add_score(
                entered_name, self.game.score, self.game.level, mode_name
            )
            self.menu.current_state = "highscores"
            self.app_state = APP_STATE_MENU
            return
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if self.name_buffer:
                self.name_buffer = self.name_buffer[:-1]
                self.sound.play_click()
        elif key != -1 and 32 <= key <= 126:
            if len(self.name_buffer) < 4:
                char = chr(key).upper()
                if char.isalnum() or char in ("-", "_"):
                    self.name_buffer += char
                    self.sound.play_click()

        highest = self.highscores.get_highest_score()
        self.renderer.render_game(self.game, highest)
        self.renderer.render_name_entry(self.game.score, self.name_buffer)

def main():
    def curses_main(stdscr):
        app = NokiaSnakeApp(stdscr)
        app.run()

    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
