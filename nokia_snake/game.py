"""
Nokia Snake Game Logic Engine.
Implements authentic movement, collision detection, food & bonus bug spawning,
speed calculation, and state tracking.
"""

import collections
import random
import time
from typing import List, Tuple, Set, Optional, Deque

from .config import (
    GRID_WIDTH, GRID_HEIGHT, INITIAL_SNAKE_LENGTH,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, OPPOSITE_DIRS,
    LEVEL_DELAYS, DYNAMIC_SPEEDUP_PER_FOOD, MIN_DELAY,
    MODE_SNAKE1, MODE_SNAKE2
)
from .mazes import Maze, get_mazes
from .audio import SoundEngine

Coord = Tuple[int, int]

class SnakeGame:
    def __init__(self, sound_engine: SoundEngine):
        self.sound = sound_engine
        self.mazes = get_mazes()

        # Game settings
        self.level = 5
        self.game_mode = MODE_SNAKE1
        self.maze_id = "snake1_classic"
        self.maze = self.mazes[self.maze_id]

        # Game state variables
        self.snake: List[Coord] = []
        self.direction: Coord = DIR_RIGHT
        self.input_queue: Deque[Coord] = collections.deque(maxlen=3)
        self.food: Coord = (0, 0)
        self.bonus_bug: Optional[Coord] = None
        self.bonus_timer: int = 0
        self.bonus_max_timer: int = 50

        self.score: int = 0
        self.foods_eaten: int = 0
        self.is_alive: bool = True
        self.is_paused: bool = False
        self.is_game_over: bool = False
        self.crash_reason: str = ""

        self.tick_delay: float = LEVEL_DELAYS[self.level]
        self.last_tick_time: float = 0.0

        # Start game
        self.reset()

    def set_mode(self, mode: str):
        self.game_mode = mode
        if mode == MODE_SNAKE1:
            self.maze_id = "snake1_classic"
        else:
            if not self.maze_id.startswith("snake2"):
                self.maze_id = "snake2_wrap"
        self.maze = self.mazes[self.maze_id]

    def set_maze(self, maze_id: str):
        if maze_id in self.mazes:
            self.maze_id = maze_id
            self.maze = self.mazes[maze_id]

    def set_level(self, level: int):
        self.level = max(1, min(9, level))
        self.tick_delay = LEVEL_DELAYS[self.level]

    def reset(self):
        """Reset the game board for a fresh round."""
        self.maze = self.mazes[self.maze_id]
        self.direction = DIR_RIGHT
        self.input_queue.clear()

        # Place initial snake of 3 segments horizontally in the center-left
        start_y = GRID_HEIGHT // 2
        start_x = 5
        self.snake = [
            (start_x, start_y),      # Head
            (start_x - 1, start_y),  # Body
            (start_x - 2, start_y),  # Tail
        ]

        self.score = 0
        self.foods_eaten = 0
        self.is_alive = True
        self.is_paused = False
        self.is_game_over = False
        self.crash_reason = ""
        self.bonus_bug = None
        self.bonus_timer = 0
        self.tick_delay = LEVEL_DELAYS[self.level]
        self.last_tick_time = time.time()

        self.spawn_food()

    def spawn_food(self):
        """Place regular food pellet in a random unoccupied cell."""
        occupied: Set[Coord] = set(self.snake) | self.maze.walls
        if self.bonus_bug:
            occupied.add(self.bonus_bug)

        available = [
            (x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
            if (x, y) not in occupied
        ]
        if available:
            self.food = random.choice(available)

    def spawn_bonus(self):
        """Spawn a bonus bug for a limited duration."""
        occupied: Set[Coord] = set(self.snake) | self.maze.walls
        occupied.add(self.food)

        available = [
            (x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
            if (x, y) not in occupied
        ]
        if available:
            self.bonus_bug = random.choice(available)
            # Duration scales with level (approx 40-60 ticks)
            self.bonus_max_timer = 45 + (10 - self.level) * 3
            self.bonus_timer = self.bonus_max_timer

    def queue_direction(self, new_dir: Coord):
        """
        Buffer direction input, preventing 180-degree self-collisions
        and buffering quick turns.
        """
        if not self.is_alive or self.is_paused:
            return

        last_dir = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir != last_dir and new_dir != OPPOSITE_DIRS.get(last_dir):
            if len(self.input_queue) < self.input_queue.maxlen:
                self.input_queue.append(new_dir)

    def toggle_pause(self):
        if self.is_alive and not self.is_game_over:
            self.is_paused = not self.is_paused
            return self.is_paused
        return False

    def update(self) -> bool:
        """
        Execute one game step if tick time has elapsed.
        Returns True if a tick was executed, False otherwise.
        """
        if not self.is_alive or self.is_paused or self.is_game_over:
            return False

        now = time.time()
        if now - self.last_tick_time < self.tick_delay:
            return False

        self.last_tick_time = now
        self._step()
        return True

    def _step(self):
        # Apply buffered direction if available
        if self.input_queue:
            self.direction = self.input_queue.popleft()

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_x = head_x + dx
        new_y = head_y + dy

        # Handle boundaries & screen wraparound
        if self.maze.has_wrap:
            new_x = new_x % GRID_WIDTH
            new_y = new_y % GRID_HEIGHT
        else:
            # Snake 1997 solid walls
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                self._crash("wall")
                return

        new_head = (new_x, new_y)

        # Check collision with internal maze walls
        if new_head in self.maze.walls:
            self._crash("wall")
            return

        # Check collision with self
        # Note: if new_head equals the current tail, and we didn't eat food,
        # the tail will vacate this position this tick.
        eating_regular = (new_head == self.food)
        body_to_check = self.snake if eating_regular else self.snake[:-1]
        if new_head in body_to_check:
            self._crash("self")
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Handle regular food consumption
        if eating_regular:
            self.foods_eaten += 1
            # In Nokia Snake: point per pellet multiplied by level
            self.score += self.level
            self.sound.play_eat()

            # Dynamic speedup
            self.tick_delay = max(MIN_DELAY, self.tick_delay - DYNAMIC_SPEEDUP_PER_FOOD)

            self.spawn_food()

            # In Snake II, bonus bug appears every 5 food items
            if self.game_mode == MODE_SNAKE2 and (self.foods_eaten % 5 == 0) and not self.bonus_bug:
                self.spawn_bonus()
        else:
            self.snake.pop()

        # Handle bonus bug consumption & countdown
        if self.bonus_bug:
            if new_head == self.bonus_bug:
                # Eating bonus awards extra score based on speed
                fraction_left = self.bonus_timer / max(1, self.bonus_max_timer)
                bonus_val = int(fraction_left * self.level * 10) + (self.level * 5)
                self.score += bonus_val
                self.sound.play_bonus()
                self.bonus_bug = None
                self.bonus_timer = 0
            else:
                self.bonus_timer -= 1
                if self.bonus_timer <= 0:
                    self.bonus_bug = None

    def _crash(self, reason: str):
        self.is_alive = False
        self.is_game_over = True
        self.crash_reason = reason
        self.sound.play_crash()
