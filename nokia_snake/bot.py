"""
Autoplay Bot for Nokia Snake demo mode.
Uses Breadth-First Search (BFS) to find safe paths to food and survive.
"""

import collections
from typing import Optional, List, Tuple, Set

from .config import (
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    GRID_WIDTH, GRID_HEIGHT, OPPOSITE_DIRS
)
from .game import SnakeGame

Coord = Tuple[int, int]
ALL_DIRS = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]

class SnakeBot:
    def __init__(self, game: SnakeGame):
        self.game = game

    def get_next_direction(self) -> Optional[Coord]:
        """Compute the next best direction using BFS pathfinding."""
        if not self.game.is_alive or self.game.is_game_over:
            return None

        head = self.game.snake[0]
        target = self.game.bonus_bug if self.game.bonus_bug else self.game.food

        # 1. Try to find shortest path to target
        path = self._bfs(head, target)
        if path and len(path) > 1:
            next_step = path[1]
            return self._coord_to_dir(head, next_step)

        # 2. If target unreachable, find any safe move that doesn't kill us immediately
        safe_moves = self._get_safe_moves(head)
        if safe_moves:
            # Pick safe move with maximum open space
            best_dir = max(safe_moves, key=lambda d: self._count_reachable_space(self._apply_dir(head, d)))
            return best_dir

        # 3. Fallback to current direction
        return self.game.direction

    def _bfs(self, start: Coord, goal: Coord) -> Optional[List[Coord]]:
        queue = collections.deque([[start]])
        visited: Set[Coord] = {start}
        obstacles = set(self.game.snake[:-1]) | self.game.maze.walls

        while queue:
            path = queue.popleft()
            curr = path[-1]

            if curr == goal:
                return path

            for d in ALL_DIRS:
                nxt = self._apply_dir(curr, d)
                if nxt is None or nxt in obstacles or nxt in visited:
                    continue
                visited.add(nxt)
                queue.append(path + [nxt])

        return None

    def _apply_dir(self, pos: Coord, d: Coord) -> Optional[Coord]:
        nx = pos[0] + d[0]
        ny = pos[1] + d[1]

        if self.game.maze.has_wrap:
            nx %= GRID_WIDTH
            ny %= GRID_HEIGHT
        else:
            if nx < 0 or nx >= GRID_WIDTH or ny < 0 or ny >= GRID_HEIGHT:
                return None

        return (nx, ny)

    def _get_safe_moves(self, head: Coord) -> List[Coord]:
        safe = []
        obstacles = set(self.game.snake[:-1]) | self.game.maze.walls
        curr_dir = self.game.direction

        for d in ALL_DIRS:
            if d == OPPOSITE_DIRS.get(curr_dir):
                continue
            nxt = self._apply_dir(head, d)
            if nxt is not None and nxt not in obstacles:
                safe.append(d)
        return safe

    def _count_reachable_space(self, start: Optional[Coord]) -> int:
        if start is None:
            return 0
        queue = collections.deque([start])
        visited = {start}
        obstacles = set(self.game.snake[:-1]) | self.game.maze.walls

        count = 0
        while queue and count < 50:
            curr = queue.popleft()
            count += 1
            for d in ALL_DIRS:
                nxt = self._apply_dir(curr, d)
                if nxt and nxt not in obstacles and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return count

    def _coord_to_dir(self, from_c: Coord, to_c: Coord) -> Coord:
        fx, fy = from_c
        tx, ty = to_c

        # Handle wraparound
        if self.game.maze.has_wrap:
            if fx == 0 and tx == GRID_WIDTH - 1:
                return DIR_LEFT
            if fx == GRID_WIDTH - 1 and tx == 0:
                return DIR_RIGHT
            if fy == 0 and ty == GRID_HEIGHT - 1:
                return DIR_UP
            if fy == GRID_HEIGHT - 1 and ty == 0:
                return DIR_DOWN

        return (tx - fx, ty - fy)
