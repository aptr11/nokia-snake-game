"""
Nokia Snake & Blockade Game Logic Engine.
Implements:
1. Snake I (1997 Nokia 6110) - Solid boundary walls, dynamic acceleration.
2. Snake II (2000 Nokia 3310) - Mazes, edge wraparound, periodic bonus insects.
3. Blockade (1976 Gremlin Arcade) - 2-Player / CPU duel with permanent growing trails.
"""

import collections
import random
import time
from typing import List, Tuple, Set, Optional, Deque

from .config import (
    GRID_WIDTH, GRID_HEIGHT, INITIAL_SNAKE_LENGTH,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, OPPOSITE_DIRS,
    LEVEL_DELAYS, DYNAMIC_SPEEDUP_PER_FOOD, MIN_DELAY,
    MODE_SNAKE1, MODE_SNAKE2, MODE_BLOCKADE,
    BLOCKADE_OPPONENT_CPU, BLOCKADE_OPPONENT_HUMAN
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

        # Player 1 state
        self.snake: List[Coord] = []
        self.direction: Coord = DIR_RIGHT
        self.input_queue: Deque[Coord] = collections.deque(maxlen=3)

        # Player 2 / CPU state (for Blockade 1976)
        self.p2_snake: List[Coord] = []
        self.p2_direction: Coord = DIR_LEFT
        self.p2_input_queue: Deque[Coord] = collections.deque(maxlen=3)
        self.blockade_opponent: str = BLOCKADE_OPPONENT_CPU
        self.p1_wins: int = 0
        self.p2_wins: int = 0
        self.round_number: int = 1
        self.match_target: int = 3
        self.round_winner: Optional[str] = None
        self.is_round_over: bool = False
        self.round_end_time: float = 0.0

        # Food & Bonus items
        self.food: Coord = (0, 0)
        self.bonus_bug: Optional[Coord] = None
        self.bonus_timer: int = 0
        self.bonus_max_timer: int = 50

        # General status
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
        elif mode == MODE_BLOCKADE:
            self.maze_id = "snake1_classic"
            self.p1_wins = 0
            self.p2_wins = 0
            self.round_number = 1
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

    def cycle_match_target(self):
        targets = [3, 5, 7]
        idx = (targets.index(self.match_target) + 1) % len(targets) if self.match_target in targets else 0
        self.match_target = targets[idx]

    def toggle_blockade_opponent(self):
        if self.blockade_opponent == BLOCKADE_OPPONENT_CPU:
            self.blockade_opponent = BLOCKADE_OPPONENT_HUMAN
        else:
            self.blockade_opponent = BLOCKADE_OPPONENT_CPU
        return self.blockade_opponent

    def reset(self):
        """Reset the game board for a fresh round or game."""
        self.maze = self.mazes[self.maze_id]
        self.direction = DIR_RIGHT
        self.input_queue.clear()
        self.p2_input_queue.clear()

        self.score = 0
        self.foods_eaten = 0
        self.is_alive = True
        self.is_paused = False
        self.is_game_over = False
        self.is_round_over = False
        self.round_winner = None
        self.crash_reason = ""
        self.bonus_bug = None
        self.bonus_timer = 0
        self.tick_delay = LEVEL_DELAYS[self.level]
        self.last_tick_time = time.time()

        if self.game_mode == MODE_BLOCKADE:
            # Blockade (1976): Players start with a single point on opposite sides
            start_y = GRID_HEIGHT // 2
            self.snake = [(3, start_y)]
            self.direction = DIR_RIGHT
            self.p2_snake = [(GRID_WIDTH - 4, start_y)]
            self.p2_direction = DIR_LEFT
            self.food = (-1, -1)
        else:
            # Standard Snake: 3 initial segments
            start_y = GRID_HEIGHT // 2
            start_x = 5
            self.snake = [
                (start_x, start_y),      # Head
                (start_x - 1, start_y),  # Body
                (start_x - 2, start_y),  # Tail
            ]
            self.p2_snake = []
            self.spawn_food()

    def start_next_round(self):
        """Start the next round in a Blockade match."""
        if self.game_mode == MODE_BLOCKADE and not self.is_game_over:
            self.round_number += 1
            start_y = GRID_HEIGHT // 2
            self.snake = [(3, start_y)]
            self.direction = DIR_RIGHT
            self.input_queue.clear()

            self.p2_snake = [(GRID_WIDTH - 4, start_y)]
            self.p2_direction = DIR_LEFT
            self.p2_input_queue.clear()

            self.is_round_over = False
            self.round_winner = None
            self.last_tick_time = time.time()

    def spawn_food(self):
        """Place regular food pellet in a random unoccupied cell."""
        if self.game_mode == MODE_BLOCKADE:
            return

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
        if self.game_mode == MODE_BLOCKADE:
            return

        occupied: Set[Coord] = set(self.snake) | self.maze.walls
        occupied.add(self.food)

        available = [
            (x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
            if (x, y) not in occupied
        ]
        if available:
            self.bonus_bug = random.choice(available)
            self.bonus_max_timer = 45 + (10 - self.level) * 3
            self.bonus_timer = self.bonus_max_timer

    def queue_direction(self, new_dir: Coord):
        """Buffer Player 1 direction input."""
        if not self.is_alive or self.is_paused or self.is_round_over:
            return

        last_dir = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir != last_dir and new_dir != OPPOSITE_DIRS.get(last_dir):
            if len(self.input_queue) < self.input_queue.maxlen:
                self.input_queue.append(new_dir)

    def queue_direction_p2(self, new_dir: Coord):
        """Buffer Player 2 / CPU direction input (Blockade)."""
        if not self.is_alive or self.is_paused or self.is_round_over:
            return

        last_dir = self.p2_input_queue[-1] if self.p2_input_queue else self.p2_direction
        if new_dir != last_dir and new_dir != OPPOSITE_DIRS.get(last_dir):
            if len(self.p2_input_queue) < self.p2_input_queue.maxlen:
                self.p2_input_queue.append(new_dir)

    def toggle_pause(self):
        if self.is_alive and not self.is_game_over:
            self.is_paused = not self.is_paused
            return self.is_paused
        return False

    def update(self) -> bool:
        """Execute one game step if tick time has elapsed."""
        if not self.is_alive or self.is_paused or self.is_game_over:
            return False

        if self.is_round_over:
            # In Blockade, wait 1.2 seconds after a round before starting next round
            if time.time() - self.round_end_time > 1.2:
                if not self.is_game_over:
                    self.start_next_round()
            return False

        now = time.time()
        if now - self.last_tick_time < self.tick_delay:
            return False

        self.last_tick_time = now
        if self.game_mode == MODE_BLOCKADE:
            self._step_blockade()
        else:
            self._step_snake()
        return True

    def _step_blockade(self):
        """Step function for Blockade (1976): dual permanent growing trails."""
        if self.input_queue:
            self.direction = self.input_queue.popleft()
        if self.p2_input_queue:
            self.p2_direction = self.p2_input_queue.popleft()

        p1_head = self.snake[0]
        p2_head = self.p2_snake[0]

        p1_next = (p1_head[0] + self.direction[0], p1_head[1] + self.direction[1])
        p2_next = (p2_head[0] + self.p2_direction[0], p2_head[1] + self.p2_direction[1])

        p1_trail = set(self.snake)
        p2_trail = set(self.p2_snake)

        # Collision check for Player 1
        p1_crash = (
            p1_next[0] < 0 or p1_next[0] >= GRID_WIDTH or
            p1_next[1] < 0 or p1_next[1] >= GRID_HEIGHT or
            p1_next in p1_trail or p1_next in p2_trail
        )

        # Collision check for Player 2
        p2_crash = (
            p2_next[0] < 0 or p2_next[0] >= GRID_WIDTH or
            p2_next[1] < 0 or p2_next[1] >= GRID_HEIGHT or
            p2_next in p1_trail or p2_next in p2_trail
        )

        # Head-on collision
        if p1_next == p2_next:
            p1_crash = True
            p2_crash = True

        if p1_crash or p2_crash:
            self.is_round_over = True
            self.round_end_time = time.time()

            if p1_crash and p2_crash:
                self.round_winner = "tie"
                self.sound.play_crash()
            elif p1_crash:
                self.p2_wins += 1
                self.round_winner = "p2"
                self.sound.play_crash()
            else:
                self.p1_wins += 1
                self.round_winner = "p1"
                self.sound.play_bonus()

            # Check if match is won
            if self.p1_wins >= self.match_target or self.p2_wins >= self.match_target:
                self.is_game_over = True
                self.sound.play_highscore()
            return

        # Both survive: advance trails (neither trail pops its tail in Blockade)
        self.snake.insert(0, p1_next)
        self.p2_snake.insert(0, p2_next)
        self.sound.play_click()

    def _step_snake(self):
        """Step function for standard Snake I and Snake II."""
        if self.input_queue:
            self.direction = self.input_queue.popleft()

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_x = head_x + dx
        new_y = head_y + dy

        if self.maze.has_wrap:
            new_x = new_x % GRID_WIDTH
            new_y = new_y % GRID_HEIGHT
        else:
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                self._crash("wall")
                return

        new_head = (new_x, new_y)

        if new_head in self.maze.walls:
            self._crash("wall")
            return

        eating_regular = (new_head == self.food)
        body_to_check = self.snake if eating_regular else self.snake[:-1]
        if new_head in body_to_check:
            self._crash("self")
            return

        self.snake.insert(0, new_head)

        if eating_regular:
            self.foods_eaten += 1
            self.score += self.level
            self.sound.play_eat()
            self.tick_delay = max(MIN_DELAY, self.tick_delay - DYNAMIC_SPEEDUP_PER_FOOD)
            self.spawn_food()

            if self.game_mode == MODE_SNAKE2 and (self.foods_eaten % 5 == 0) and not self.bonus_bug:
                self.spawn_bonus()
        else:
            self.snake.pop()

        if self.bonus_bug:
            if new_head == self.bonus_bug:
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
