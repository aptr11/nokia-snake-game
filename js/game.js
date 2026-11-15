/**
 * Nokia Snake & Blockade: Web Game Logic Engine.
 * Supports Snake 1997, Snake II, and Blockade 1976.
 */

const GRID_W = 20;
const GRID_H = 10;

const DIR_UP = { x: 0, y: -1 };
const DIR_DOWN = { x: 0, y: 1 };
const DIR_LEFT = { x: -1, y: 0 };
const DIR_RIGHT = { x: 1, y: 0 };

const LEVEL_DELAYS_MS = {
  1: 260, 2: 225, 3: 190, 4: 160, 5: 130,
  6: 105, 7: 85,  8: 65,  9: 48
};

function isOpposite(d1, d2) {
  return d1.x === -d2.x && d1.y === -d2.y;
}

// 5 Mazes for Snake II
const MAZES = {
  snake1_classic: {
    name: "Classic 1997",
    hasWrap: false,
    walls: new Set()
  },
  snake2_wrap: {
    name: "Maze 1: Open Wrap",
    hasWrap: true,
    walls: new Set()
  },
  snake2_tunnel: {
    name: "Maze 2: Tunnel",
    hasWrap: true,
    walls: (() => {
      const s = new Set();
      [0, 1, 8, 9].forEach(y => { s.add(`6,${y}`); s.add(`13,${y}`); });
      return s;
    })()
  },
  snake2_corners: {
    name: "Maze 3: Fortresses",
    hasWrap: true,
    walls: (() => {
      const s = new Set();
      [3, 4, 15, 16].forEach(x => {
        [2, 3, 6, 7].forEach(y => { s.add(`${x},${y}`); });
      });
      return s;
    })()
  },
  snake2_rails: {
    name: "Maze 4: Double Rails",
    hasWrap: true,
    walls: (() => {
      const s = new Set();
      for (let x = 4; x <= 15; x++) {
        if (x !== 9 && x !== 10) {
          s.add(`${x},2`);
          s.add(`${x},7`);
        }
      }
      return s;
    })()
  },
  snake2_laby: {
    name: "Maze 5: Labyrinth",
    hasWrap: true,
    walls: (() => {
      const s = new Set();
      for (let y = 1; y <= 8; y++) if (y !== 5) s.add(`9,${y}`);
      for (let x = 3; x <= 7; x++) { s.add(`${x},1`); s.add(`${x},8`); }
      for (let x = 12; x <= 16; x++) { s.add(`${x},1`); s.add(`${x},8`); }
      return s;
    })()
  }
};

class GameEngine {
  constructor(sound) {
    this.sound = sound;

    // Settings
    this.level = 5;
    this.mode = "snake1"; // "snake1", "snake2", "blockade"
    this.mazeId = "snake1_classic";
    this.maze = MAZES[this.mazeId];

    // Player 1
    this.snake = [];
    this.dir = DIR_RIGHT;
    this.queue = [];

    // Player 2 / CPU (Blockade)
    this.p2Snake = [];
    this.p2Dir = DIR_LEFT;
    this.p2Queue = [];
    this.blockadeOpponent = "cpu"; // "cpu" or "human"
    this.p1Wins = 0;
    this.p2Wins = 0;
    this.roundNumber = 1;
    this.matchTarget = 3;
    this.roundWinner = null;
    this.isRoundOver = false;
    this.roundEndTime = 0;

    // Items
    this.food = { x: 0, y: 0 };
    this.bonus = null;
    this.bonusTimer = 0;
    this.bonusMax = 50;

    // State
    this.score = 0;
    this.foodsEaten = 0;
    this.isAlive = true;
    this.isPaused = false;
    this.isGameOver = false;

    this.tickDelay = LEVEL_DELAYS_MS[this.level];
    this.lastTick = 0;

    this.reset();
  }

  setMode(mode) {
    this.mode = mode;
    if (mode === "snake1") {
      this.mazeId = "snake1_classic";
    } else if (mode === "blockade") {
      this.mazeId = "snake1_classic";
      this.p1Wins = 0;
      this.p2Wins = 0;
      this.roundNumber = 1;
    } else {
      if (!this.mazeId.startsWith("snake2")) {
        this.mazeId = "snake2_wrap";
      }
    }
    this.maze = MAZES[this.mazeId];
  }

  setMaze(mazeId) {
    if (MAZES[mazeId]) {
      this.mazeId = mazeId;
      this.maze = MAZES[mazeId];
    }
  }

  setLevel(lvl) {
    this.level = Math.max(1, Math.min(9, lvl));
    this.tickDelay = LEVEL_DELAYS_MS[this.level];
  }

  reset() {
    this.maze = MAZES[this.mazeId];
    this.dir = DIR_RIGHT;
    this.queue = [];
    this.p2Queue = [];

    this.score = 0;
    this.foodsEaten = 0;
    this.isAlive = true;
    this.isPaused = false;
    this.isGameOver = false;
    this.isRoundOver = false;
    this.roundWinner = null;
    this.bonus = null;
    this.bonusTimer = 0;
    this.tickDelay = LEVEL_DELAYS_MS[this.level];
    this.lastTick = performance.now();

    if (this.mode === "blockade") {
      this.snake = [{ x: 3, y: 5 }];
      this.dir = DIR_RIGHT;
      this.p2Snake = [{ x: 16, y: 5 }];
      this.p2Dir = DIR_LEFT;
      this.food = { x: -1, y: -1 };
    } else {
      this.snake = [
        { x: 5, y: 5 },
        { x: 4, y: 5 },
        { x: 3, y: 5 }
      ];
      this.p2Snake = [];
      this.spawnFood();
    }
  }

  startNextRound() {
    if (this.mode === "blockade" && !this.isGameOver) {
      this.roundNumber++;
      this.snake = [{ x: 3, y: 5 }];
      this.dir = DIR_RIGHT;
      this.queue = [];

      this.p2Snake = [{ x: 16, y: 5 }];
      this.p2Dir = DIR_LEFT;
      this.p2Queue = [];

      this.isRoundOver = false;
      this.roundWinner = null;
      this.lastTick = performance.now();
    }
  }

  spawnFood() {
    if (this.mode === "blockade") return;
    const occupied = new Set(this.snake.map(p => `${p.x},${p.y}`));
    for (const w of this.maze.walls) occupied.add(w);
    if (this.bonus) occupied.add(`${this.bonus.x},${this.bonus.y}`);

    const avail = [];
    for (let x = 0; x < GRID_W; x++) {
      for (let y = 0; y < GRID_H; y++) {
        if (!occupied.has(`${x},${y}`)) avail.push({ x, y });
      }
    }
    if (avail.length > 0) {
      this.food = avail[Math.floor(Math.random() * avail.length)];
    }
  }

  spawnBonus() {
    if (this.mode === "blockade") return;
    const occupied = new Set(this.snake.map(p => `${p.x},${p.y}`));
    for (const w of this.maze.walls) occupied.add(w);
    occupied.add(`${this.food.x},${this.food.y}`);

    const avail = [];
    for (let x = 0; x < GRID_W; x++) {
      for (let y = 0; y < GRID_H; y++) {
        if (!occupied.has(`${x},${y}`)) avail.push({ x, y });
      }
    }
    if (avail.length > 0) {
      this.bonus = avail[Math.floor(Math.random() * avail.length)];
      this.bonusMax = 45 + (10 - this.level) * 3;
      this.bonusTimer = this.bonusMax;
    }
  }

  queueDirection(newDir) {
    if (!this.isAlive || this.isPaused || this.isRoundOver) return;
    const last = this.queue.length > 0 ? this.queue[this.queue.length - 1] : this.dir;
    if (newDir.x !== last.x || newDir.y !== last.y) {
      if (!isOpposite(newDir, last) && this.queue.length < 3) {
        this.queue.push(newDir);
      }
    }
  }

  queueDirectionP2(newDir) {
    if (!this.isAlive || this.isPaused || this.isRoundOver) return;
    const last = this.p2Queue.length > 0 ? this.p2Queue[this.p2Queue.length - 1] : this.p2Dir;
    if (newDir.x !== last.x || newDir.y !== last.y) {
      if (!isOpposite(newDir, last) && this.p2Queue.length < 3) {
        this.p2Queue.push(newDir);
      }
    }
  }

  togglePause() {
    if (this.isAlive && !this.isGameOver) {
      this.isPaused = !this.isPaused;
      return this.isPaused;
    }
    return false;
  }

  update(now) {
    if (!this.isAlive || this.isPaused || this.isGameOver) return false;

    if (this.isRoundOver) {
      if (now - this.roundEndTime > 1200) {
        if (!this.isGameOver) this.startNextRound();
      }
      return false;
    }

    if (now - this.lastTick < this.tickDelay) return false;

    this.lastTick = now;
    if (this.mode === "blockade") {
      this._stepBlockade();
    } else {
      this._stepSnake();
    }
    return true;
  }

  _stepBlockade() {
    if (this.queue.length > 0) this.dir = this.queue.shift();
    if (this.p2Queue.length > 0) this.p2Dir = this.p2Queue.shift();

    const p1Head = this.snake[0];
    const p2Head = this.p2Snake[0];

    const p1Next = { x: p1Head.x + this.dir.x, y: p1Head.y + this.dir.y };
    const p2Next = { x: p2Head.x + this.p2Dir.x, y: p2Head.y + this.p2Dir.y };

    const p1Trail = new Set(this.snake.map(p => `${p.x},${p.y}`));
    const p2Trail = new Set(this.p2Snake.map(p => `${p.x},${p.y}`));

    let p1Crash = (
      p1Next.x < 0 || p1Next.x >= GRID_W ||
      p1Next.y < 0 || p1Next.y >= GRID_H ||
      p1Trail.has(`${p1Next.x},${p1Next.y}`) ||
      p2Trail.has(`${p1Next.x},${p1Next.y}`)
    );

    let p2Crash = (
      p2Next.x < 0 || p2Next.x >= GRID_W ||
      p2Next.y < 0 || p2Next.y >= GRID_H ||
      p1Trail.has(`${p2Next.x},${p2Next.y}`) ||
      p2Trail.has(`${p2Next.x},${p2Next.y}`)
    );

    if (p1Next.x === p2Next.x && p1Next.y === p2Next.y) {
      p1Crash = true;
      p2Crash = true;
    }

    if (p1Crash || p2Crash) {
      this.isRoundOver = true;
      this.roundEndTime = performance.now();

      if (p1Crash && p2Crash) {
        this.roundWinner = "tie";
        this.sound.playCrash();
      } else if (p1Crash) {
        this.p2Wins++;
        this.roundWinner = "p2";
        this.sound.playCrash();
      } else {
        this.p1Wins++;
        this.roundWinner = "p1";
        this.sound.playBonus();
      }

      if (this.p1Wins >= this.matchTarget || this.p2Wins >= this.matchTarget) {
        this.isGameOver = true;
        this.sound.playHighScore();
      }
      return;
    }

    this.snake.unshift(p1Next);
    this.p2Snake.unshift(p2Next);
    this.sound.playClick();
  }

  _stepSnake() {
    if (this.queue.length > 0) this.dir = this.queue.shift();

    const head = this.snake[0];
    let nx = head.x + this.dir.x;
    let ny = head.y + this.dir.y;

    if (this.maze.hasWrap) {
      nx = (nx + GRID_W) % GRID_W;
      ny = (ny + GRID_H) % GRID_H;
    } else {
      if (nx < 0 || nx >= GRID_W || ny < 0 || ny >= GRID_H) {
        this._crash();
        return;
      }
    }

    if (this.maze.walls.has(`${nx},${ny}`)) {
      this._crash();
      return;
    }

    const eating = (nx === this.food.x && ny === this.food.y);
    const bodyToCheck = eating ? this.snake : this.snake.slice(0, -1);
    if (bodyToCheck.some(p => p.x === nx && p.y === ny)) {
      this._crash();
      return;
    }

    this.snake.unshift({ x: nx, y: ny });

    if (eating) {
      this.foodsEaten++;
      this.score += this.level;
      this.sound.playEat();
      this.tickDelay = Math.max(32, this.tickDelay - 1.2);
      this.spawnFood();

      if (this.mode === "snake2" && this.foodsEaten % 5 === 0 && !this.bonus) {
        this.spawnBonus();
      }
    } else {
      this.snake.pop();
    }

    if (this.bonus) {
      if (nx === this.bonus.x && ny === this.bonus.y) {
        const frac = this.bonusTimer / Math.max(1, this.bonusMax);
        this.score += Math.floor(frac * this.level * 10) + (this.level * 5);
        this.sound.playBonus();
        this.bonus = null;
        this.bonusTimer = 0;
      } else {
        this.bonusTimer--;
        if (this.bonusTimer <= 0) this.bonus = null;
      }
    }
  }

  _crash() {
    this.isAlive = false;
    this.isGameOver = true;
    this.sound.playCrash();
  }
}
