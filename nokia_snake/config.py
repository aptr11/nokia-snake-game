"""
Configuration and constants for Nokia Snake emulation.
Faithfully modeled on Taneli Armanto's 1997 original for Nokia 6110 / 3310.
"""

from typing import Dict, Any, Tuple

VERSION = "1.0.0"

# Dimensions
GRID_WIDTH = 20
GRID_HEIGHT = 10
BLOCK_CHAR_WIDTH = 2  # Each grid cell is 2 terminal columns wide for ~1:1 square aspect ratio

# Speed delay in seconds for starting levels 1 through 9
LEVEL_DELAYS: Dict[int, float] = {
    1: 0.260,
    2: 0.225,
    3: 0.190,
    4: 0.160,
    5: 0.130,
    6: 0.105,
    7: 0.085,
    8: 0.065,
    9: 0.048,
}

# Dynamic acceleration: reduction in tick delay per food eaten
DYNAMIC_SPEEDUP_PER_FOOD = 0.0012
MIN_DELAY = 0.032

# Initial snake length
INITIAL_SNAKE_LENGTH = 3

# Directions (dx, dy)
DIR_UP: Tuple[int, int] = (0, -1)
DIR_DOWN: Tuple[int, int] = (0, 1)
DIR_LEFT: Tuple[int, int] = (-1, 0)
DIR_RIGHT: Tuple[int, int] = (1, 0)

# OPPOSITES for preventing 180-degree suicide
OPPOSITE_DIRS = {
    DIR_UP: DIR_DOWN,
    DIR_DOWN: DIR_UP,
    DIR_LEFT: DIR_RIGHT,
    DIR_RIGHT: DIR_LEFT,
}

# Theme definitions
# Each theme defines:
#   lcd_bg: terminal 256-color index
#   lcd_fg: terminal 256-color index
#   phone_bg: phone chassis color
#   phone_fg: phone chassis text/highlights
#   rgb_hint: (r, g, b) for RGB capable terminals
THEMES = {
    "classic_green": {
        "name": "Nokia 3310 Green",
        "desc": "Iconic monochrome green LCD backlight",
        "lcd_bg": 150,     # #afd787 retro olive green
        "lcd_fg": 16,      # #000000 black pixels
        "phone_body": 24,  # #005f87 classic Nokia dark cyan/navy
        "phone_fg": 254,   # light silver text
        "keypad_bg": 236,  # dark charcoal buttons
        "keypad_fg": 252,  # white/silver button text
        "accent": 107,     # darker green
    },
    "monochrome": {
        "name": "Nokia 3210 Silver/Grey",
        "desc": "Crisp monochrome silver-grey LCD",
        "lcd_bg": 250,     # silver grey
        "lcd_fg": 233,     # deep charcoal black
        "phone_body": 240, # silver/grey body
        "phone_fg": 255,   # crisp white
        "keypad_bg": 237,  # button body
        "keypad_fg": 253,  # button text
        "accent": 244,
    },
    "matrix": {
        "name": "Nokia 8110 Neo Matrix",
        "desc": "Dark phosphor CRT green",
        "lcd_bg": 16,      # jet black
        "lcd_fg": 46,      # neon phosphor green
        "phone_body": 234, # matte obsidian black
        "phone_fg": 46,    # neon green highlights
        "keypad_bg": 235,  # dark grey keys
        "keypad_fg": 46,   # green symbols
        "accent": 40,
    },
    "amber": {
        "name": "Amber Retro 90s",
        "desc": "Warm retro amber gold display",
        "lcd_bg": 214,     # warm amber gold
        "lcd_fg": 234,     # deep brown-black
        "phone_body": 235, # dark vintage case
        "phone_fg": 220,   # gold text
        "keypad_bg": 236,  # dark keys
        "keypad_fg": 221,  # amber button text
        "accent": 178,
    },
}

DEFAULT_THEME = "classic_green"

# Game Modes
MODE_SNAKE1 = "snake1"  # 1997 Nokia 6110: Solid boundary walls, no wraparound
MODE_SNAKE2 = "snake2"  # 2000 Nokia 3310: Mazes, wraparound edges, bonus bugs

# View Modes
VIEW_PHONE = "phone"  # Render complete Nokia 3310 phone frame
VIEW_LCD = "lcd"      # Pure full retro LCD screen
