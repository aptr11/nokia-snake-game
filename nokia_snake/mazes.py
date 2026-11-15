"""
Maze layouts and border definitions for Nokia Snake I and Snake II.
Grid dimensions: 20 columns (0..19) x 10 rows (0..9).
"""

from typing import Set, Tuple, List, Dict

Coord = Tuple[int, int]

class Maze:
    def __init__(self, name: str, desc: str, has_wrap: bool, walls: Set[Coord]):
        self.name = name
        self.desc = desc
        self.has_wrap = has_wrap
        self.walls = walls  # Set of (x, y) coordinates that represent solid obstacle blocks

def get_mazes() -> Dict[str, Maze]:
    """
    Returns available mazes.
    Snake starts at x=3..5, y=5. Walls are kept away from starting area.
    """
    mazes = {}

    # --- Snake I (Original 1997) ---
    # Solid border walls, no internal obstacles, no wraparound.
    mazes["snake1_classic"] = Maze(
        name="Classic 1997",
        desc="Original Nokia 6110 solid boundary walls",
        has_wrap=False,
        walls=set()
    )

    # --- Snake II (Nokia 3310 Mazes) ---
    # Maze 1: Open Wrap - wrap through edges, no interior obstacles
    mazes["snake2_wrap"] = Maze(
        name="Maze 1: Open Wrap",
        desc="No walls; wrap around edges (Nokia 3310)",
        has_wrap=True,
        walls=set()
    )

    # Maze 2: Tunnel / Gates
    # Two vertical pillars with openings top, center, bottom
    walls_tunnel: Set[Coord] = set()
    for y in [0, 1, 8, 9]:
        walls_tunnel.add((6, y))
        walls_tunnel.add((13, y))
    mazes["snake2_tunnel"] = Maze(
        name="Maze 2: Tunnel",
        desc="Vertical gate pillars with open screen wrap",
        has_wrap=True,
        walls=walls_tunnel
    )

    # Maze 3: Corner Blocks
    # Obstacle islands in four quadrants
    walls_corners: Set[Coord] = set()
    for x in [3, 4]:
        for y in [2, 3]:
            walls_corners.add((x, y))
            walls_corners.add((x, y + 4))
    for x in [15, 16]:
        for y in [2, 3]:
            walls_corners.add((x, y))
            walls_corners.add((x, y + 4))
    mazes["snake2_corners"] = Maze(
        name="Maze 3: Fortresses",
        desc="Four corner obstacle blocks with wrap",
        has_wrap=True,
        walls=walls_corners
    )

    # Maze 4: Rails / Lanes
    # Horizontal dividers creating upper and lower lanes
    walls_rails: Set[Coord] = set()
    for x in range(4, 16):
        if x not in (9, 10):  # Gap in the center
            walls_rails.add((x, 2))
            walls_rails.add((x, 7))
    mazes["snake2_rails"] = Maze(
        name="Maze 4: Double Rails",
        desc="Dual lane dividers with center pass-through",
        has_wrap=True,
        walls=walls_rails
    )

    # Maze 5: Labyrinth
    walls_laby: Set[Coord] = set()
    for y in range(1, 9):
        if y != 5:  # Keep snake starting row free
            walls_laby.add((9, y))
    for x in range(3, 8):
        walls_laby.add((x, 1))
        walls_laby.add((x, 8))
    for x in range(12, 17):
        walls_laby.add((x, 1))
        walls_laby.add((x, 8))
    mazes["snake2_laby"] = Maze(
        name="Maze 5: Labyrinth",
        desc="Complex inner labyrinth walls",
        has_wrap=True,
        walls=walls_laby
    )

    return mazes
