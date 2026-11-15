"""
Autoplay Bot for Nokia Snake & Blockade CPU Opponent.
Uses Breadth-First Search (BFS) and flood-fill space maximization.
"""

import collections
from typing import Optional, List, Tuple, Set

from .config import (
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    GRID_WIDTH, GRID_HEIGHT, OPPOSITE_DIRS, MODE_BLOCKADE
)
from .game import SnakeGame

Coord = Tuple[int, int]
ALL_DIRS = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]

class SnakeBot:
    def __init__(self, game: SnakeGame):
        self.game = game

    def get_next_direction(self) -> Optional[Coord]:
        """Compute the next best direction for Player 1 (Snake)."""
        if not self.game.is_alive or self.game.is_game_over:
            return None

        head = self.game.snake[0]

        if self.game.game_mode == MODE_BLOCKADE:
            # In Blockade, maximize survival space
            return self._best_survival_direction(head, self.game.direction, is_p1=True)

        target = self.game.bonus_bug if self.game.bonus_bug else self.game.food

        # 1. Try to find shortest path to target
        path = self._bfs(head, target)
        if path and len(path) > 1:
            next_step = path[1]
            return self._coord_to_dir(head, next_step)

        # 2. If target unreachable, find any safe move that doesn't kill us immediately
        safe_moves = self._get_safe_moves(head, self.game.direction)
        if safe_moves:
            best_dir = max(safe_moves, key=lambda d: self._count_reachable_space(self._apply_dir(head, d)))
            return best_dir

        return self.game.direction

    def get_next_direction_p2(self) -> Optional[Coord]:
        """Compute the next best direction for Player 2 / CPU in Blockade."""
        if not self.game.is_alive or self.game.is_game_over or not self.game.p2_snake:
            return None

        p2_head = self.game.p2_snake[0]
        return self._best_survival_direction(p2_head, self.game.p2_direction, is_p1=False)

    def _best_survival_direction(self, head: Coord, curr_dir: Coord, is_p1: bool) -> Coord:
        obstacles = set(self.game.snake) | set(self.game.p2_snake) | self.game.maze.walls
        safe_moves = []

        for d in ALL_DIRS:
            if d == OPPOSITE_DIRS.get(curr_dir):
                continue
            nxt = self._apply_dir(head, d)
            if nxt is not None and nxt not in obstacles:
                # Calculate reachable free space
                space = self._count_reachable_space_custom(nxt, obstacles)
                safe_moves.append((d, space))

        if safe_moves:
            # Sort by largest space; if tied, prefer continuing in current direction
            safe_moves.sort(key=lambda item: (item[1], 1 if item[0] == curr_dir else 0), reverse=True)
            return safe_moves[0][0]

        return curr_dir

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

    def _get_safe_moves(self, head: Coord, curr_dir: Coord) -> List[Coord]:
        safe = []
        obstacles = set(self.game.snake[:-1]) | self.game.maze.walls

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
        obstacles = set(self.game.snake[:-1]) | self.game.maze.walls
        return self._count_reachable_space_custom(start, obstacles)

    def _count_reachable_space_custom(self, start: Optional[Coord], obstacles: Set[Coord]) -> int:
        if start is None or start in obstacles:
            return 0
        queue = collections.deque([start])
        visited = {start}

        count = 0
        while queue and count < 60:
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
