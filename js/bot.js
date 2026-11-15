/**
 * Autonomous Pathfinding AI Bot for Web Snake & Blockade CPU.
 */

class WebSnakeBot {
  constructor(game) {
    this.game = game;
  }

  getNextDirection() {
    if (!this.game.isAlive || this.game.isGameOver) return null;
    const head = this.game.snake[0];

    if (this.game.mode === "blockade") {
      return this._bestSurvivalDir(head, this.game.dir, true);
    }

    const target = this.game.bonus ? this.game.bonus : this.game.food;
    const path = this._bfs(head, target);
    if (path && path.length > 1) {
      const nextStep = path[1];
      return this._stepToDir(head, nextStep);
    }

    const safeMoves = this._getSafeMoves(head, this.game.dir);
    if (safeMoves.length > 0) {
      safeMoves.sort((a, b) => {
        const sA = this._countSpace(this._applyDir(head, a));
        const sB = this._countSpace(this._applyDir(head, b));
        return sB - sA;
      });
      return safeMoves[0];
    }

    return this.game.dir;
  }

  getNextDirectionP2() {
    if (!this.game.isAlive || this.game.isGameOver || this.game.p2Snake.length === 0) return null;
    const head = this.game.p2Snake[0];
    return this._bestSurvivalDir(head, this.game.p2Dir, false);
  }

  _bestSurvivalDir(head, currDir) {
    const obstacles = new Set(this.game.snake.map(p => `${p.x},${p.y}`));
    for (const p of this.game.p2Snake) obstacles.add(`${p.x},${p.y}`);
    for (const w of this.game.maze.walls) obstacles.add(w);

    const dirs = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT];
    const safeMoves = [];

    for (const d of dirs) {
      if (isOpposite(d, currDir)) continue;
      const nxt = this._applyDir(head, d);
      if (nxt && !obstacles.has(`${nxt.x},${nxt.y}`)) {
        const space = this._countSpaceObstacles(nxt, obstacles);
        safeMoves.push({ dir: d, space });
      }
    }

    if (safeMoves.length > 0) {
      safeMoves.sort((a, b) => b.space - a.space);
      return safeMoves[0].dir;
    }
    return currDir;
  }

  _bfs(start, goal) {
    const queue = [[start]];
    const visited = new Set([`${start.x},${start.y}`]);
    const obstacles = new Set(this.game.snake.slice(0, -1).map(p => `${p.x},${p.y}`));
    for (const w of this.game.maze.walls) obstacles.add(w);

    const dirs = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT];

    while (queue.length > 0) {
      const path = queue.shift();
      const curr = path[path.length - 1];

      if (curr.x === goal.x && curr.y === goal.y) return path;

      for (const d of dirs) {
        const nxt = this._applyDir(curr, d);
        if (!nxt || obstacles.has(`${nxt.x},${nxt.y}`) || visited.has(`${nxt.x},${nxt.y}`)) continue;

        visited.add(`${nxt.x},${nxt.y}`);
        queue.push([...path, nxt]);
      }
    }
    return null;
  }

  _applyDir(pos, d) {
    let nx = pos.x + d.x;
    let ny = pos.y + d.y;

    if (this.game.maze.hasWrap) {
      nx = (nx + GRID_W) % GRID_W;
      ny = (ny + GRID_H) % GRID_H;
    } else {
      if (nx < 0 || nx >= GRID_W || ny < 0 || ny >= GRID_H) return null;
    }
    return { x: nx, y: ny };
  }

  _getSafeMoves(head, currDir) {
    const safe = [];
    const obstacles = new Set(this.game.snake.slice(0, -1).map(p => `${p.x},${p.y}`));
    for (const w of this.game.maze.walls) obstacles.add(w);

    const dirs = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT];
    for (const d of dirs) {
      if (isOpposite(d, currDir)) continue;
      const nxt = this._applyDir(head, d);
      if (nxt && !obstacles.has(`${nxt.x},${nxt.y}`)) safe.push(d);
    }
    return safe;
  }

  _countSpace(start) {
    if (!start) return 0;
    const obstacles = new Set(this.game.snake.slice(0, -1).map(p => `${p.x},${p.y}`));
    for (const w of this.game.maze.walls) obstacles.add(w);
    return this._countSpaceObstacles(start, obstacles);
  }

  _countSpaceObstacles(start, obstacles) {
    if (!start || obstacles.has(`${start.x},${start.y}`)) return 0;
    const queue = [start];
    const visited = new Set([`${start.x},${start.y}`]);
    const dirs = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT];
    let count = 0;

    while (queue.length > 0 && count < 60) {
      const curr = queue.shift();
      count++;
      for (const d of dirs) {
        const nxt = this._applyDir(curr, d);
        if (nxt && !obstacles.has(`${nxt.x},${nxt.y}`) && !visited.has(`${nxt.x},${nxt.y}`)) {
          visited.add(`${nxt.x},${nxt.y}`);
          queue.push(nxt);
        }
      }
    }
    return count;
  }

  _stepToDir(from, to) {
    if (this.game.maze.hasWrap) {
      if (from.x === 0 && to.x === GRID_W - 1) return DIR_LEFT;
      if (from.x === GRID_W - 1 && to.x === 0) return DIR_RIGHT;
      if (from.y === 0 && to.y === GRID_H - 1) return DIR_UP;
      if (from.y === GRID_H - 1 && to.y === 0) return DIR_DOWN;
    }
    return { x: to.x - from.x, y: to.y - from.y };
  }
}
