"""
Nokia Display and curses renderer.
Renders both the Nokia 3310 Phone Bezel mode and Full Retro LCD mode.
Supports multiple Nokia LCD color themes, menu rendering, dialogs, and animations.
"""

import curses
import time
from typing import List, Tuple, Dict, Any, Optional

from .config import (
    GRID_WIDTH, GRID_HEIGHT, THEMES, DEFAULT_THEME,
    VIEW_PHONE, VIEW_LCD, MODE_SNAKE1, MODE_SNAKE2, MODE_BLOCKADE,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT
)
from .game import SnakeGame
from .highscores import HighScoreManager

Coord = Tuple[int, int]

# Color pair IDs
PAIR_LCD_NORMAL = 1
PAIR_LCD_INVERSE = 2
PAIR_LCD_ACCENT = 3
PAIR_PHONE_BODY = 4
PAIR_PHONE_KEYPAD = 5
PAIR_PHONE_ACTIVE_KEY = 6
PAIR_WALL = 7
PAIR_BONUS = 8
PAIR_LOGO = 9

class Renderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.theme_name = DEFAULT_THEME
        self.view_mode = VIEW_PHONE
        self.has_colors = False
        self.active_key: Optional[str] = None
        self.active_key_time: float = 0.0

        self._init_colors()

    def _init_colors(self):
        """Initialize curses color pairs for the active theme."""
        try:
            curses.curs_set(0)
        except (curses.error, Exception):
            pass

        try:
            self.has_colors = curses.has_colors()
        except (curses.error, Exception):
            self.has_colors = False

        if not self.has_colors:
            return

        try:
            curses.start_color()
            can_256 = curses.COLORS >= 256
            theme = THEMES.get(self.theme_name, THEMES[DEFAULT_THEME])

            if can_256:
                lcd_bg = theme["lcd_bg"]
                lcd_fg = theme["lcd_fg"]
                phone_body = theme["phone_body"]
                phone_fg = theme["phone_fg"]
                keypad_bg = theme["keypad_bg"]
                keypad_fg = theme["keypad_fg"]
                accent = theme["accent"]

                curses.init_pair(PAIR_LCD_NORMAL, lcd_fg, lcd_bg)
                curses.init_pair(PAIR_LCD_INVERSE, lcd_bg, lcd_fg)
                curses.init_pair(PAIR_LCD_ACCENT, accent, lcd_bg)
                curses.init_pair(PAIR_PHONE_BODY, phone_fg, phone_body)
                curses.init_pair(PAIR_PHONE_KEYPAD, keypad_fg, keypad_bg)
                curses.init_pair(PAIR_PHONE_ACTIVE_KEY, keypad_bg, keypad_fg)
                curses.init_pair(PAIR_WALL, lcd_fg, lcd_bg)
                curses.init_pair(PAIR_BONUS, lcd_fg, lcd_bg)
                curses.init_pair(PAIR_LOGO, phone_fg, phone_body)
            else:
                # 8-color fallback
                curses.init_pair(PAIR_LCD_NORMAL, curses.COLOR_BLACK, curses.COLOR_GREEN)
                curses.init_pair(PAIR_LCD_INVERSE, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(PAIR_LCD_ACCENT, curses.COLOR_BLACK, curses.COLOR_GREEN)
                curses.init_pair(PAIR_PHONE_BODY, curses.COLOR_WHITE, curses.COLOR_BLUE)
                curses.init_pair(PAIR_PHONE_KEYPAD, curses.COLOR_BLACK, curses.COLOR_WHITE)
                curses.init_pair(PAIR_PHONE_ACTIVE_KEY, curses.COLOR_WHITE, curses.COLOR_BLACK)
                curses.init_pair(PAIR_WALL, curses.COLOR_BLACK, curses.COLOR_GREEN)
                curses.init_pair(PAIR_BONUS, curses.COLOR_BLACK, curses.COLOR_GREEN)
                curses.init_pair(PAIR_LOGO, curses.COLOR_WHITE, curses.COLOR_BLUE)
        except (curses.error, Exception):
            self.has_colors = False

    def set_theme(self, theme_key: str):
        if theme_key in THEMES:
            self.theme_name = theme_key
            self._init_colors()

    def cycle_theme(self) -> str:
        keys = list(THEMES.keys())
        idx = (keys.index(self.theme_name) + 1) % len(keys)
        self.set_theme(keys[idx])
        return THEMES[self.theme_name]["name"]

    def toggle_view(self) -> str:
        self.view_mode = VIEW_LCD if self.view_mode == VIEW_PHONE else VIEW_PHONE
        return self.view_mode

    def highlight_key(self, key_name: str):
        self.active_key = key_name
        self.active_key_time = time.time()

    def get_attr(self, pair_id: int, extra=0) -> int:
        if self.has_colors:
            return curses.color_pair(pair_id) | extra
        return extra

    # -------------------------------------------------------------
    # Safe Drawing Helpers
    # -------------------------------------------------------------

    def safe_addstr(self, y: int, x: int, text: str, attr: int = 0):
        max_y, max_x = self.stdscr.getmaxyx()
        if y < 0 or y >= max_y or x >= max_x:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        avail = max_x - x
        if avail <= 0:
            return
        to_draw = text[:avail]
        # In curses, writing the bottom-right character can cause a scroll/ERR
        if y == max_y - 1 and len(to_draw) >= avail:
            to_draw = to_draw[:-1]
        try:
            self.stdscr.addstr(y, x, to_draw, attr)
        except curses.error:
            pass

    # -------------------------------------------------------------
    # Render Game Board
    # -------------------------------------------------------------

    def render_game(self, game: SnakeGame, highscore: int):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        # If terminal is too small for Phone Bezel, force Full LCD mode
        active_view = self.view_mode
        if active_view == VIEW_PHONE and (max_x < 60 or max_y < 24):
            active_view = VIEW_LCD

        if active_view == VIEW_PHONE:
            self._render_phone_view(game, highscore)
        else:
            self._render_lcd_fullscreen(game, highscore)

        self.stdscr.refresh()

    def _render_phone_view(self, game: SnakeGame, highscore: int):
        max_y, max_x = self.stdscr.getmaxyx()

        # Phone frame lines (width: 58, height: 23)
        phone_width = 58
        phone_height = 23
        start_x = max(0, (max_x - phone_width) // 2)
        start_y = max(0, (max_y - phone_height) // 2)

        # Draw phone bezel casing
        body_attr = self.get_attr(PAIR_PHONE_BODY)
        logo_attr = self.get_attr(PAIR_LOGO, curses.A_BOLD)
        key_attr = self.get_attr(PAIR_PHONE_KEYPAD)
        act_attr = self.get_attr(PAIR_PHONE_ACTIVE_KEY, curses.A_BOLD)
        lcd_attr = self.get_attr(PAIR_LCD_NORMAL)

        # Phone Chassis Template
        chassis = [
            (0,  r"        .----------------------------------------.        ", body_attr),
            (1,  r"       /                  NOKIA                   \       ", body_attr),
            (2,  r"      |                  [||||]                    |      ", body_attr),
            (3,  r"     .-+------------------------------------------+-.     ", body_attr),
            (16, r"     .-+------------------------------------------+-.     ", body_attr),
            (17, r"      |             (--- NAVI KEY ---)             |      ", body_attr),
            (18, r"      |          [ 1 ]    [ 2▲]    [ 3 ]           |      ", body_attr),
            (19, r"      |          [ 4◄]    [ 5 ]    [ 6►]           |      ", body_attr),
            (20, r"      |          [ 7 ]    [ 8▼]    [ 9 ]           |      ", body_attr),
            (21, r"      |          [ * ]    [ 0_]    [ # ]           |      ", body_attr),
            (22, r"       \__________________________________________/       ", body_attr),
        ]

        # Draw chassis elements
        for rel_y, line, attr in chassis:
            self.safe_addstr(start_y + rel_y, start_x, line, attr)

        # Emphasize NOKIA logo
        self.safe_addstr(start_y + 1, start_x + 26, "NOKIA", logo_attr)

        # Check for active keypad glow
        now = time.time()
        is_active = (now - self.active_key_time < 0.20)
        if is_active and self.active_key:
            # Highlight matching button on keypad
            key_positions = {
                "2": (start_y + 18, start_x + 26, "[ 2▲]"),
                "UP": (start_y + 18, start_x + 26, "[ 2▲]"),
                "4": (start_y + 19, start_x + 17, "[ 4◄]"),
                "LEFT": (start_y + 19, start_x + 17, "[ 4◄]"),
                "6": (start_y + 19, start_x + 35, "[ 6►]"),
                "RIGHT": (start_y + 19, start_x + 35, "[ 6►]"),
                "8": (start_y + 20, start_x + 26, "[ 8▼]"),
                "DOWN": (start_y + 20, start_x + 26, "[ 8▼]"),
                "NAVI": (start_y + 17, start_x + 20, "(--- NAVI KEY ---)"),
            }
            if self.active_key in key_positions:
                ky, kx, ktext = key_positions[self.active_key]
                self.safe_addstr(ky, kx, ktext, act_attr)

        # Draw LCD Side Borders
        for row in range(4, 16):
            self.safe_addstr(start_y + row, start_x, "     | |", body_attr)
            self.safe_addstr(start_y + row, start_x + 48, "| |     ", body_attr)

        # Inside LCD screen: starts at start_x + 8, start_y + 4. Width: 40 chars.
        lcd_x = start_x + 8
        lcd_y = start_y + 4
        self._render_lcd_contents(lcd_y, lcd_x, game, highscore)

        # Footer control hint
        hint = "[Q] Menu  [P] Pause  [M] Sound  [V] View  [T] Theme"
        hint_x = max(0, (max_x - len(hint)) // 2)
        self.safe_addstr(max_y - 1, hint_x, hint, self.get_attr(PAIR_LCD_ACCENT, curses.A_DIM))

    def _render_lcd_fullscreen(self, game: SnakeGame, highscore: int):
        max_y, max_x = self.stdscr.getmaxyx()

        box_width = 42
        box_height = 14
        start_x = max(0, (max_x - box_width) // 2)
        start_y = max(0, (max_y - box_height) // 2)

        lcd_attr = self.get_attr(PAIR_LCD_NORMAL)
        inv_attr = self.get_attr(PAIR_LCD_INVERSE)

        # Top border
        self.safe_addstr(start_y, start_x, "." + "-" * (box_width - 2) + ".", lcd_attr)

        # Side borders
        for row in range(1, box_height - 1):
            self.safe_addstr(start_y + row, start_x, "|", lcd_attr)
            self.safe_addstr(start_y + row, start_x + box_width - 1, "|", lcd_attr)

        # Bottom border
        self.safe_addstr(start_y + box_height - 1, start_x, "'" + "-" * (box_width - 2) + "'", lcd_attr)

        # LCD Content inside
        lcd_x = start_x + 1
        lcd_y = start_y + 1
        self._render_lcd_contents(lcd_y, lcd_x, game, highscore)

        # Footer control hint
        hint = "[2/▲ 8/▼ 4/◄ 6/►] Move  [P] Pause  [V] Phone Frame  [M] Sound  [Q] Menu"
        hint_x = max(0, (max_x - len(hint)) // 2)
        self.safe_addstr(max_y - 1, hint_x, hint, self.get_attr(PAIR_LCD_ACCENT, curses.A_DIM))

    def _render_lcd_contents(self, lcd_y: int, lcd_x: int, game: SnakeGame, highscore: int):
        """Render the 40-character wide, 12-line Nokia LCD display."""
        normal_attr = self.get_attr(PAIR_LCD_NORMAL)
        inv_attr = self.get_attr(PAIR_LCD_INVERSE, curses.A_BOLD)
        bonus_attr = self.get_attr(PAIR_BONUS, curses.A_BOLD)

        # Row 0: Top Status Bar
        if game.game_mode == MODE_BLOCKADE:
            p2_name = "CPU" if game.blockade_opponent == "cpu" else "P2"
            left = f"ıll P1:{game.p1_wins:02d}"
            right = f"{p2_name}:{game.p2_wins:02d} [■■■■]"
            center_len = 40 - len(left) - len(right)
            center_msg = f"RND {game.round_number}/{game.match_target}"
            center = f"{center_msg:^{center_len}}"
            status_line = left + center + right
            self.safe_addstr(lcd_y, lcd_x, status_line[:40], normal_attr)
        else:
            score_str = f"{game.score:04d}"
            lvl_str = f"L{game.level}"
            if game.bonus_bug:
                bar_len = int((game.bonus_timer / max(1, game.bonus_max_timer)) * 6)
                center_msg = f"★[{'■' * bar_len}{' ' * (6 - bar_len)}]"
            elif game.is_paused:
                center_msg = "[PAUSED]"
            else:
                center_msg = f"HI: {highscore:04d}"

            left = f"ıll {score_str}"
            right = f"{lvl_str} [■■■■]"
            center_len = 40 - len(left) - len(right)
            center = f"{center_msg:^{center_len}}"
            status_line = left + center + right
            self.safe_addstr(lcd_y, lcd_x, status_line[:40], normal_attr)

        # Row 1: Divider line
        div_char = "-" if not game.maze.has_wrap else "="
        self.safe_addstr(lcd_y + 1, lcd_x, div_char * 40, normal_attr)

        # Rows 2..11: The 20x10 Playfield (each cell is 2 characters wide)
        p1_head = game.snake[0] if game.snake else None
        p1_body = set(game.snake[1:]) if len(game.snake) > 1 else set()
        p2_head = game.p2_snake[0] if game.p2_snake else None
        p2_body = set(game.p2_snake[1:]) if len(game.p2_snake) > 1 else set()
        maze_walls = game.maze.walls

        for gy in range(GRID_HEIGHT):
            row_chars = []
            for gx in range(GRID_WIDTH):
                pos = (gx, gy)
                if pos == p1_head:
                    dx, dy = game.direction
                    cell = "►█" if dx == 1 else ("█◄" if dx == -1 else ("▲█" if dy == -1 else "▼█"))
                elif pos in p1_body:
                    cell = "██"
                elif pos == p2_head:
                    dx, dy = game.p2_direction
                    cell = "►▒" if dx == 1 else ("▒◄" if dx == -1 else ("▲▒" if dy == -1 else "▼▒"))
                elif pos in p2_body:
                    cell = "▒▒"
                elif pos == game.food and game.game_mode != MODE_BLOCKADE:
                    cell = "◆ "
                elif pos == game.bonus_bug and game.game_mode != MODE_BLOCKADE:
                    cell = "※ "
                elif pos in maze_walls:
                    cell = "▒▒"
                else:
                    cell = "  "
                row_chars.append(cell)

            line_str = "".join(row_chars)
            self.safe_addstr(lcd_y + 2 + gy, lcd_x, line_str, normal_attr)

        # Blockade Round Over overlay
        if game.game_mode == MODE_BLOCKADE and game.is_round_over and not game.is_game_over:
            if game.round_winner == "tie":
                round_box = "[  ROUND TIED!  ]"
            elif game.round_winner == "p1":
                round_box = "[  P1 SCORES!   ]"
            else:
                opp_name = "CPU" if game.blockade_opponent == "cpu" else "P2"
                round_box = f"[  {opp_name} SCORES!   ]"
            box_x = lcd_x + (40 - len(round_box)) // 2
            box_y = lcd_y + 6
            self.safe_addstr(box_y, box_x, round_box, inv_attr)

        # If Paused overlay
        if game.is_paused:
            pause_box = "[  P A U S E D  ]"
            box_x = lcd_x + (40 - len(pause_box)) // 2
            box_y = lcd_y + 6
            self.safe_addstr(box_y, box_x, pause_box, inv_attr)

    # -------------------------------------------------------------
    # Crash Flash Animation
    # -------------------------------------------------------------

    def flash_crash(self):
        """Screen flash invert effect on snake death."""
        for _ in range(2):
            self.stdscr.bkgd(' ', self.get_attr(PAIR_LCD_INVERSE))
            self.stdscr.refresh()
            time.sleep(0.08)
            self.stdscr.bkgd(' ', self.get_attr(PAIR_LCD_NORMAL))
            self.stdscr.refresh()
            time.sleep(0.08)

    # -------------------------------------------------------------
    # Render Menu in LCD
    # -------------------------------------------------------------

    def render_menu(self, menu_title: str, items: List[str], selected_idx: int, footer_hint: str = ""):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        active_view = self.view_mode
        if active_view == VIEW_PHONE and (max_x < 60 or max_y < 24):
            active_view = VIEW_LCD

        if active_view == VIEW_PHONE:
            self._render_phone_menu(menu_title, items, selected_idx, footer_hint)
        else:
            self._render_lcd_fullscreen_menu(menu_title, items, selected_idx, footer_hint)

        self.stdscr.refresh()

    def _render_phone_menu(self, menu_title: str, items: List[str], selected_idx: int, footer_hint: str):
        max_y, max_x = self.stdscr.getmaxyx()
        phone_width = 58
        phone_height = 23
        start_x = max(0, (max_x - phone_width) // 2)
        start_y = max(0, (max_y - phone_height) // 2)

        body_attr = self.get_attr(PAIR_PHONE_BODY)
        logo_attr = self.get_attr(PAIR_LOGO, curses.A_BOLD)
        key_attr = self.get_attr(PAIR_PHONE_KEYPAD)

        chassis = [
            (0,  r"        .----------------------------------------.        ", body_attr),
            (1,  r"       /                  NOKIA                   \       ", body_attr),
            (2,  r"      |                  [||||]                    |      ", body_attr),
            (3,  r"     .-+------------------------------------------+-.     ", body_attr),
            (16, r"     .-+------------------------------------------+-.     ", body_attr),
            (17, r"      |             (--- SELECT ---)               |      ", body_attr),
            (18, r"      |          [ 1 ]    [ 2▲]    [ 3 ]           |      ", body_attr),
            (19, r"      |          [ 4◄]    [ 5 ]    [ 6►]           |      ", body_attr),
            (20, r"      |          [ 7 ]    [ 8▼]    [ 9 ]           |      ", body_attr),
            (21, r"      |          [ * ]    [ 0_]    [ # ]           |      ", body_attr),
            (22, r"       \__________________________________________/       ", body_attr),
        ]
        for rel_y, line, attr in chassis:
            self.safe_addstr(start_y + rel_y, start_x, line, attr)

        self.safe_addstr(start_y + 1, start_x + 26, "NOKIA", logo_attr)

        for row in range(4, 16):
            self.safe_addstr(start_y + row, start_x, "     | |", body_attr)
            self.safe_addstr(start_y + row, start_x + 48, "| |     ", body_attr)

        lcd_x = start_x + 8
        lcd_y = start_y + 4
        self._render_menu_lcd_area(lcd_y, lcd_x, menu_title, items, selected_idx)

        hint = footer_hint or "[2/8/▲/▼] Navigate  [Enter/5] Select  [Q/Esc] Back"
        hint_x = max(0, (max_x - len(hint)) // 2)
        self.safe_addstr(max_y - 1, hint_x, hint, self.get_attr(PAIR_LCD_ACCENT, curses.A_DIM))

    def _render_lcd_fullscreen_menu(self, menu_title: str, items: List[str], selected_idx: int, footer_hint: str):
        max_y, max_x = self.stdscr.getmaxyx()
        box_width = 42
        box_height = 14
        start_x = max(0, (max_x - box_width) // 2)
        start_y = max(0, (max_y - box_height) // 2)

        lcd_attr = self.get_attr(PAIR_LCD_NORMAL)

        self.safe_addstr(start_y, start_x, "." + "-" * (box_width - 2) + ".", lcd_attr)
        for row in range(1, box_height - 1):
            self.safe_addstr(start_y + row, start_x, "|", lcd_attr)
            self.safe_addstr(start_y + row, start_x + box_width - 1, "|", lcd_attr)
        self.safe_addstr(start_y + box_height - 1, start_x, "'" + "-" * (box_width - 2) + "'", lcd_attr)

        lcd_x = start_x + 1
        lcd_y = start_y + 1
        self._render_menu_lcd_area(lcd_y, lcd_x, menu_title, items, selected_idx)

        hint = footer_hint or "[2/8/▲/▼] Navigate  [Enter/5] Select  [V] View  [Q/Esc] Back"
        hint_x = max(0, (max_x - len(hint)) // 2)
        self.safe_addstr(max_y - 1, hint_x, hint, self.get_attr(PAIR_LCD_ACCENT, curses.A_DIM))

    def _render_menu_lcd_area(self, lcd_y: int, lcd_x: int, menu_title: str, items: List[str], selected_idx: int):
        normal_attr = self.get_attr(PAIR_LCD_NORMAL)
        inv_attr = self.get_attr(PAIR_LCD_INVERSE, curses.A_BOLD)

        # Header
        left = "ıll"
        right = "[■■■■]"
        center_len = 40 - len(left) - len(right)
        center = f"{menu_title:^{center_len}}"
        top_bar = left + center + right
        self.safe_addstr(lcd_y, lcd_x, top_bar[:40], normal_attr)
        self.safe_addstr(lcd_y + 1, lcd_x, "-" * 40, normal_attr)

        # Calculate menu scrolling if items > 9
        max_visible = 9
        scroll_start = 0
        if len(items) > max_visible:
            scroll_start = max(0, min(selected_idx - max_visible // 2, len(items) - max_visible))

        visible_items = items[scroll_start:scroll_start + max_visible]

        # Render menu items
        for i, item in enumerate(visible_items):
            actual_idx = scroll_start + i
            is_selected = (actual_idx == selected_idx)
            item_y = lcd_y + 2 + i

            if is_selected:
                line_text = f" > {item}"
                # Render full width highlight bar
                padded = f"{line_text:<38}  "
                self.safe_addstr(item_y, lcd_x, padded[:40], inv_attr)
            else:
                line_text = f"   {item}"
                padded = f"{line_text:<40}"
                self.safe_addstr(item_y, lcd_x, padded[:40], normal_attr)

        # Clear remaining lines in LCD
        for clear_i in range(len(visible_items), 10):
            self.safe_addstr(lcd_y + 2 + clear_i, lcd_x, " " * 40, normal_attr)

    def get_lcd_origin(self) -> Tuple[int, int]:
        max_y, max_x = self.stdscr.getmaxyx()
        active_view = self.view_mode
        if active_view == VIEW_PHONE and (max_x < 60 or max_y < 24):
            active_view = VIEW_LCD

        if active_view == VIEW_PHONE:
            phone_width = 58
            phone_height = 23
            start_x = max(0, (max_x - phone_width) // 2)
            start_y = max(0, (max_y - phone_height) // 2)
            return (start_y + 4, start_x + 8)
        else:
            box_width = 42
            box_height = 14
            start_x = max(0, (max_x - box_width) // 2)
            start_y = max(0, (max_y - box_height) // 2)
            return (start_y + 1, start_x + 1)

    # -------------------------------------------------------------
    # Dialogs & Overlays
    # -------------------------------------------------------------

    def render_game_over(self, game_or_score, highscore: int, is_new_record: bool):
        lcd_y, lcd_x = self.get_lcd_origin()
        inv_attr = self.get_attr(PAIR_LCD_INVERSE, curses.A_BOLD)
        norm_attr = self.get_attr(PAIR_LCD_NORMAL)

        is_blockade = hasattr(game_or_score, "game_mode") and game_or_score.game_mode == MODE_BLOCKADE
        score = game_or_score.score if hasattr(game_or_score, "score") else game_or_score

        if is_blockade:
            p2_name = "CPU" if game_or_score.blockade_opponent == "cpu" else "P2"
            winner_str = "P1 WINS MATCH!" if game_or_score.p1_wins >= game_or_score.match_target else f"{p2_name} WINS MATCH!"
            lines = [
                "============================",
                f"    {winner_str:^20}    ",
                "============================",
                "       FINAL SCORE:         ",
                f"   P1: {game_or_score.p1_wins}    vs    {p2_name}: {game_or_score.p2_wins}  ",
                "                            ",
                " [Press Any Key to Continue]",
                "============================",
            ]
        else:
            lines = [
                "============================",
                "      G A M E   O V E R     ",
                "============================",
                f"   SCORE:        {score:05d}      ",
                f"   RECORD:       {highscore:05d}      ",
            ]
            if is_new_record:
                lines.append("    ★ NEW HIGH SCORE! ★     ")
            else:
                lines.append("                            ")
            lines.append(" [Press Any Key to Continue]")
            lines.append("============================")

        box_width = 28
        start_x = lcd_x + (40 - box_width) // 2
        start_y = lcd_y + 2 + (10 - len(lines)) // 2

        for i, l in enumerate(lines):
            attr = inv_attr if i in (1, 5) else norm_attr
            self.safe_addstr(start_y + i, start_x, l, attr)

        self.stdscr.refresh()

    def render_name_entry(self, score: int, current_name: str):
        lcd_y, lcd_x = self.get_lcd_origin()
        inv_attr = self.get_attr(PAIR_LCD_INVERSE, curses.A_BOLD)
        norm_attr = self.get_attr(PAIR_LCD_NORMAL)

        lines = [
            "============================",
            "    ★ NEW HIGH SCORE! ★     ",
            "============================",
            f"        SCORE: {score:05d}        ",
            "       ENTER INITIALS:      ",
            f"           [ {current_name:^3} ]          ",
            "   [Enter:Save  Del:Back]   ",
            "============================",
        ]

        box_width = 28
        start_x = lcd_x + (40 - box_width) // 2
        start_y = lcd_y + 2 + (10 - len(lines)) // 2

        for i, l in enumerate(lines):
            attr = inv_attr if i in (1, 5) else norm_attr
            self.safe_addstr(start_y + i, start_x, l, attr)

        self.stdscr.refresh()
