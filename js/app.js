/**
 * Main Web Application Controller for Nokia Snake & Blockade.
 */

// Themes Palette
const THEMES_PALETTE = {
  classic_green: { name: "Nokia 3310 Green", bg: "#9bbc0f", fg: "#0f380f", accent: "#8bac0f" },
  monochrome:    { name: "Nokia 3210 Silver", bg: "#c8d0c0", fg: "#1f241d", accent: "#b0b8a8" },
  matrix:        { name: "Neo Matrix",       bg: "#000000", fg: "#00ff41", accent: "#00cc33" },
  amber:         { name: "Amber Retro 90s",  bg: "#e6a122", fg: "#2c1a00", accent: "#c98816" }
};

class NokiaWebApp {
  constructor() {
    this.canvas = document.getElementById("gameCanvas");
    this.ctx = this.canvas.getContext("2d");

    // Internal virtual resolution: 40 columns x 12 rows (matching Nokia terminal LCD)
    this.cols = 40;
    this.rows = 12;
    this.charW = 8;
    this.charH = 14;
    this.canvas.width = this.cols * this.charW;   // 320px
    this.canvas.height = this.rows * this.charH; // 168px

    this.sound = new WebSoundEngine();
    this.game = new GameEngine(this.sound);
    this.bot = new WebSnakeBot(this.game);

    this.themeKey = "classic_green";
    this.appState = "menu"; // "menu", "playing", "game_over", "name_entry", "highscores", "help"
    this.menuIndex = 0;
    this.hasActiveGame = false;
    this.demoMode = false;

    // High Scores in localStorage
    this.highscores = this._loadHighScores();
    this.nameBuffer = "";

    this._bindEvents();
    this._startLoop();

    // Play startup tune on first user click anywhere
    document.addEventListener("click", () => {
      if (!this._startupPlayed) {
        this._startupPlayed = true;
        this.sound.playNokiaTune();
      }
    }, { once: true });
  }

  _loadHighScores() {
    try {
      const saved = localStorage.getItem("nokia_snake_scores");
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return [
      { name: "TNA", score: 500, level: 9 },
      { name: "NOK", score: 331, level: 7 },
      { name: "SNK", score: 240, level: 5 },
      { name: "331", score: 180, level: 4 },
      { name: "RET", score: 120, level: 3 }
    ];
  }

  _saveHighScores() {
    try {
      localStorage.setItem("nokia_snake_scores", JSON.stringify(this.highscores));
    } catch (e) {}
  }

  _addHighScore(name, score, level) {
    this.highscores.push({
      name: (name.trim().toUpperCase() || "YOU").slice(0, 4),
      score,
      level
    });
    this.highscores.sort((a, b) => b.score - a.score);
    this.highscores = this.highscores.slice(0, 10);
    this._saveHighScores();
  }

  setTheme(themeKey) {
    if (THEMES_PALETTE[themeKey]) {
      this.themeKey = themeKey;
      document.body.setAttribute("data-theme", themeKey);
    }
  }

  cycleTheme() {
    const keys = Object.keys(THEMES_PALETTE);
    const idx = (keys.indexOf(this.themeKey) + 1) % keys.length;
    this.setTheme(keys[idx]);
  }

  toggleViewMode() {
    document.body.classList.toggle("view-lcd-only");
  }

  getMenuItems() {
    const items = [];
    if (this.hasActiveGame && !this.game.isGameOver) {
      items.push({ label: "1. Continue", action: "continue" });
    }
    items.push({ label: "New Game", action: "new_game" });
    items.push({ label: `Skill Level: < ${this.game.level} >`, action: "level" });

    const mLabel = this.game.mode === "snake1" ? "Snake 1997" : (this.game.mode === "snake2" ? "Snake II" : "Blockade 1976");
    items.push({ label: `Game Mode: < ${mLabel} >`, action: "mode" });

    if (this.game.mode === "snake2") {
      items.push({ label: `Maze: < ${this.game.maze.name} >`, action: "maze" });
    } else if (this.game.mode === "blockade") {
      const oppLabel = this.game.blockadeOpponent === "cpu" ? "vs CPU" : "2-Player Local";
      items.push({ label: `Opponent: < ${oppLabel} >`, action: "blockade_opp" });
      items.push({ label: `Match: < First to ${this.game.matchTarget} >`, action: "blockade_target" });
    }

    items.push({ label: "High Scores", action: "highscores" });
    items.push({ label: `Theme: < ${THEMES_PALETTE[this.themeKey].name.split(" ")[0]} >`, action: "theme" });
    items.push({ label: `Sound: < ${this.sound.enabled ? "ON" : "OFF"} >`, action: "sound" });
    items.push({ label: "Instructions", action: "help" });
    return items;
  }

  _bindEvents() {
    // Keyboard Listener
    window.addEventListener("keydown", (e) => this._handleKeyDown(e));

    // Onscreen Buttons
    document.querySelectorAll("[data-key]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const k = btn.getAttribute("data-key");
        this._handleAction(k);
        this._flashBtn(btn);
      });
    });

    // Touch Swipe on Canvas
    let touchStartX = 0, touchStartY = 0;
    this.canvas.addEventListener("touchstart", (e) => {
      if (e.touches.length > 0) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    this.canvas.addEventListener("touchend", (e) => {
      if (e.changedTouches.length > 0) {
        const dx = e.changedTouches[0].clientX - touchStartX;
        const dy = e.changedTouches[0].clientY - touchStartY;
        const absX = Math.abs(dx);
        const absY = Math.abs(dy);

        if (Math.max(absX, absY) > 20) {
          if (absX > absY) {
            this._handleAction(dx > 0 ? "RIGHT" : "LEFT");
          } else {
            this._handleAction(dy > 0 ? "DOWN" : "UP");
          }
        } else {
          // Tap acts as Select/Navi
          this._handleAction("SELECT");
        }
      }
    }, { passive: true });
  }

  _flashBtn(btn) {
    btn.classList.add("btn-active-glow");
    setTimeout(() => btn.classList.remove("btn-active-glow"), 150);
  }

  _flashKeyById(id) {
    const el = document.querySelector(`[data-key="${id}"]`);
    if (el) this._flashBtn(el);
  }

  _handleKeyDown(e) {
    const code = e.code;
    const key = e.key.toUpperCase();

    // Prevent scrolling with arrows/space
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(code)) {
      e.preventDefault();
    }

    if (this.appState === "name_entry") {
      if (code === "Enter") {
        this._addHighScore(this.nameBuffer, this.game.score, this.game.level);
        this.appState = "highscores";
        this.sound.playClick();
      } else if (code === "Backspace") {
        this.nameBuffer = this.nameBuffer.slice(0, -1);
        this.sound.playClick();
      } else if (key.length === 1 && /[A-Z0-9]/.test(key) && this.nameBuffer.length < 4) {
        this.nameBuffer += key;
        this.sound.playClick();
      }
      return;
    }

    if (this.appState === "highscores" || this.appState === "help") {
      this.appState = "menu";
      this.sound.playClick();
      return;
    }

    if (this.appState === "game_over") {
      const topScore = this.highscores.length > 0 ? this.highscores[0].score : 0;
      if (this.game.mode !== "blockade" && (this.highscores.length < 10 || this.game.score > this.highscores[this.highscores.length - 1].score)) {
        this.nameBuffer = "";
        this.appState = "name_entry";
        this.sound.playHighScore();
      } else {
        this.appState = "menu";
        this.sound.playClick();
      }
      return;
    }

    // In-game Hotkeys
    if (code === "KeyP" || code === "Space") {
      if (this.appState === "playing") {
        this.game.togglePause();
        this.sound.playClick();
        return;
      }
    }
    if (code === "KeyV") { this.toggleViewMode(); return; }
    if (code === "KeyT") { this.cycleTheme(); return; }
    if (code === "KeyM") { this.sound.toggle(); return; }
    if (code === "KeyQ" || code === "Escape") {
      if (this.appState === "playing") {
        this.game.isPaused = true;
        this.appState = "menu";
        this.hasActiveGame = true;
        this.menuIndex = 0;
        return;
      }
    }

    // Blockade 2-Player controls
    const isBlockade2P = (this.game.mode === "blockade" && this.game.blockadeOpponent === "human");
    if (this.appState === "playing" && isBlockade2P) {
      // P1: WASD / 2,4,6,8
      if (code === "KeyW" || key === "2") { this.game.queueDirection(DIR_UP); this._flashKeyById("UP"); }
      else if (code === "KeyS" || key === "8") { this.game.queueDirection(DIR_DOWN); this._flashKeyById("DOWN"); }
      else if (code === "KeyA" || key === "4") { this.game.queueDirection(DIR_LEFT); this._flashKeyById("LEFT"); }
      else if (code === "KeyD" || key === "6") { this.game.queueDirection(DIR_RIGHT); this._flashKeyById("RIGHT"); }

      // P2: Arrows / IJKL
      else if (code === "ArrowUp" || code === "KeyI") this.game.queueDirectionP2(DIR_UP);
      else if (code === "ArrowDown" || code === "KeyK") this.game.queueDirectionP2(DIR_DOWN);
      else if (code === "ArrowLeft" || code === "KeyJ") this.game.queueDirectionP2(DIR_LEFT);
      else if (code === "ArrowRight" || code === "KeyL") this.game.queueDirectionP2(DIR_RIGHT);
      return;
    }

    // General Directional actions
    if (code === "ArrowUp" || key === "2" || code === "KeyW" || code === "KeyK") this._handleAction("UP");
    else if (code === "ArrowDown" || key === "8" || code === "KeyS" || code === "KeyJ") this._handleAction("DOWN");
    else if (code === "ArrowLeft" || key === "4" || code === "KeyA" || code === "KeyH") this._handleAction("LEFT");
    else if (code === "ArrowRight" || key === "6" || code === "KeyD" || code === "KeyL") this._handleAction("RIGHT");
    else if (code === "Enter" || code === "Space" || key === "5") this._handleAction("SELECT");
    else if (code === "KeyC") this._handleAction("BACK");
  }

  _handleAction(action) {
    if (this.appState === "menu") {
      const items = this.getMenuItems();
      if (action === "UP") {
        this.sound.playClick();
        this._flashKeyById("UP");
        this.menuIndex = (this.menuIndex - 1 + items.length) % items.length;
      } else if (action === "DOWN") {
        this.sound.playClick();
        this._flashKeyById("DOWN");
        this.menuIndex = (this.menuIndex + 1) % items.length;
      } else if (action === "LEFT") {
        this.sound.playClick();
        this._flashKeyById("LEFT");
        this._adjustMenuItem(items[this.menuIndex], -1);
      } else if (action === "RIGHT") {
        this.sound.playClick();
        this._flashKeyById("RIGHT");
        this._adjustMenuItem(items[this.menuIndex], 1);
      } else if (action === "SELECT") {
        this.sound.playClick();
        this._flashKeyById("SELECT");
        this._selectMenuItem(items[this.menuIndex]);
      }
    } else if (this.appState === "playing") {
      this.demoMode = false;
      if (action === "UP") { this.game.queueDirection(DIR_UP); this._flashKeyById("UP"); }
      else if (action === "DOWN") { this.game.queueDirection(DIR_DOWN); this._flashKeyById("DOWN"); }
      else if (action === "LEFT") { this.game.queueDirection(DIR_LEFT); this._flashKeyById("LEFT"); }
      else if (action === "RIGHT") { this.game.queueDirection(DIR_RIGHT); this._flashKeyById("RIGHT"); }
      else if (action === "SELECT") { this.game.togglePause(); this.sound.playClick(); }
      else if (action === "BACK") { this.appState = "menu"; this.game.isPaused = true; this.hasActiveGame = true; }
    } else if (this.appState === "game_over" || this.appState === "highscores" || this.appState === "help") {
      this.appState = "menu";
      this.sound.playClick();
    }
  }

  _adjustMenuItem(item, delta) {
    if (!item) return;
    if (item.action === "level") {
      this.game.setLevel(this.game.level + delta === 0 ? 9 : (this.game.level + delta === 10 ? 1 : this.game.level + delta));
    } else if (item.action === "mode") {
      const modes = ["snake1", "snake2", "blockade"];
      const idx = (modes.indexOf(this.game.mode) + delta + modes.length) % modes.length;
      this.game.setMode(modes[idx]);
    } else if (item.action === "maze") {
      const keys = Object.keys(MAZES).filter(k => k.startsWith("snake2"));
      const idx = (keys.indexOf(this.game.mazeId) + delta + keys.length) % keys.length;
      this.game.setMaze(keys[idx]);
    } else if (item.action === "blockade_opp") {
      this.game.blockadeOpponent = (this.game.blockadeOpponent === "cpu" ? "human" : "cpu");
    } else if (item.action === "blockade_target") {
      const targets = [3, 5, 7];
      const idx = (targets.indexOf(this.game.matchTarget) + delta + targets.length) % targets.length;
      this.game.matchTarget = targets[idx];
    } else if (item.action === "theme") {
      this.cycleTheme();
    } else if (item.action === "sound") {
      this.sound.toggle();
    }
  }

  _selectMenuItem(item) {
    if (!item) return;
    if (item.action === "continue") {
      this.game.isPaused = false;
      this.appState = "playing";
    } else if (item.action === "new_game") {
      this.game.reset();
      this.hasActiveGame = true;
      this.appState = "playing";
    } else if (item.action === "highscores") {
      this.appState = "highscores";
    } else if (item.action === "help") {
      this.appState = "help";
    } else {
      this._adjustMenuItem(item, 1);
    }
  }

  _startLoop() {
    const loop = (now) => {
      this._update(now);
      this._render();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  _update(now) {
    if (this.appState === "playing") {
      const isBlockadeCPU = (this.game.mode === "blockade" && this.game.blockadeOpponent === "cpu");

      if (!this.game.isPaused && !this.game.isRoundOver) {
        if (this.demoMode && this.game.mode !== "blockade") {
          const d = this.bot.getNextDirection();
          if (d) this.game.queueDirection(d);
        } else if (isBlockadeCPU) {
          const d2 = this.bot.getNextDirectionP2();
          if (d2) this.game.queueDirectionP2(d2);
        }
      }

      this.game.update(now);

      if (this.game.isGameOver) {
        this.appState = "game_over";
        this.hasActiveGame = false;
      }
    }
  }

  _render() {
    const p = THEMES_PALETTE[this.themeKey];
    this.ctx.fillStyle = p.bg;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    if (this.appState === "menu") {
      this._renderMenu();
    } else if (this.appState === "playing" || this.appState === "game_over" || this.appState === "name_entry") {
      this._renderGame();
      if (this.appState === "game_over") this._renderGameOverOverlay();
      if (this.appState === "name_entry") this._renderNameEntryOverlay();
    } else if (this.appState === "highscores") {
      this._renderHighScores();
    } else if (this.appState === "help") {
      this._renderHelp();
    }
  }

  _drawText(text, col, row, isInverse = false) {
    const p = THEMES_PALETTE[this.themeKey];
    const x = col * this.charW;
    const y = row * this.charH;

    if (isInverse) {
      this.ctx.fillStyle = p.fg;
      this.ctx.fillRect(x, y, text.length * this.charW, this.charH);
      this.ctx.fillStyle = p.bg;
    } else {
      this.ctx.fillStyle = p.fg;
    }

    this.ctx.font = '12px "Courier New", monospace';
    this.ctx.textBaseline = "middle";
    this.ctx.fillText(text, x, y + this.charH / 2);
  }

  _renderMenu() {
    const p = THEMES_PALETTE[this.themeKey];
    this._drawText("ıll" + "S N A K E".padStart(19).padEnd(31) + "[■■■■]", 0, 0);

    // Divider
    this._drawText("-".repeat(40), 0, 1);

    const items = this.getMenuItems();
    const visibleCount = 9;
    let startIdx = 0;
    if (items.length > visibleCount) {
      startIdx = Math.max(0, Math.min(this.menuIndex - Math.floor(visibleCount / 2), items.length - visibleCount));
    }

    for (let i = 0; i < visibleCount && startIdx + i < items.length; i++) {
      const idx = startIdx + i;
      const isSel = (idx === this.menuIndex);
      const label = (isSel ? ` > ${items[idx].label}` : `   ${items[idx].label}`).padEnd(40).slice(0, 40);
      this._drawText(label, 0, 2 + i, isSel);
    }
  }

  _renderGame() {
    const p = THEMES_PALETTE[this.themeKey];
    const topScore = this.highscores.length > 0 ? this.highscores[0].score : 0;

    // Header Status Bar (40 chars)
    if (this.game.mode === "blockade") {
      const p2 = this.game.blockadeOpponent === "cpu" ? "CPU" : "P2";
      const left = `ıll P1:${String(this.game.p1Wins).padStart(2, "0")}`;
      const right = `${p2}:${String(this.game.p2Wins).padStart(2, "0")} [■■■■]`;
      const mid = `RND ${this.game.roundNumber}/${this.game.matchTarget}`;
      const centerLen = 40 - left.length - right.length;
      const full = left + mid.padStart(Math.floor((centerLen + mid.length) / 2)).padEnd(centerLen) + right;
      this._drawText(full.slice(0, 40), 0, 0);
    } else {
      const scoreStr = String(this.game.score).padStart(4, "0");
      let mid = this.game.isPaused ? "[PAUSED]" : `HI: ${String(topScore).padStart(4, "0")}`;
      if (this.game.bonus) {
        const barLen = Math.floor((this.game.bonusTimer / Math.max(1, this.game.bonusMax)) * 6);
        mid = `★[${"■".repeat(barLen)}${" ".repeat(6 - barLen)}]`;
      }
      const left = `ıll ${scoreStr}`;
      const right = `L${this.game.level} [■■■■]`;
      const centerLen = 40 - left.length - right.length;
      const full = left + mid.padStart(Math.floor((centerLen + mid.length) / 2)).padEnd(centerLen) + right;
      this._drawText(full.slice(0, 40), 0, 0);
    }

    // Divider line
    this._drawText((this.game.maze.hasWrap ? "=" : "-").repeat(40), 0, 1);

    // Playfield: 20x10 blocks (each block is 2 chars = 16x14 px)
    const blockW = this.charW * 2;
    const blockH = this.charH;
    const startY = 2 * this.charH;

    // Maze walls
    this.ctx.fillStyle = p.fg;
    for (const w of this.game.maze.walls) {
      const [wx, wy] = w.split(",").map(Number);
      this.ctx.fillRect(wx * blockW + 1, startY + wy * blockH + 1, blockW - 2, blockH - 2);
    }

    // Regular Food
    if (this.game.mode !== "blockade" && this.game.food.x >= 0) {
      const fx = this.game.food.x * blockW + blockW / 2;
      const fy = startY + this.game.food.y * blockH + blockH / 2;
      this.ctx.fillRect(fx - 4, fy - 4, 8, 8);
    }

    // Bonus bug
    if (this.game.bonus) {
      const bx = this.game.bonus.x * blockW + 2;
      const by = startY + this.game.bonus.y * blockH + 2;
      this.ctx.fillRect(bx, by, blockW - 4, blockH - 4);
    }

    // P1 Snake
    for (let i = 0; i < this.game.snake.length; i++) {
      const seg = this.game.snake[i];
      const sx = seg.x * blockW + 1;
      const sy = startY + seg.y * blockH + 1;
      this.ctx.fillStyle = p.fg;
      this.ctx.fillRect(sx, sy, blockW - 2, blockH - 2);
    }

    // P2 Snake (Blockade)
    for (let i = 0; i < this.game.p2Snake.length; i++) {
      const seg = this.game.p2Snake[i];
      const sx = seg.x * blockW + 2;
      const sy = startY + seg.y * blockH + 2;
      this.ctx.fillStyle = p.accent;
      this.ctx.fillRect(sx, sy, blockW - 4, blockH - 4);
    }

    // Paused message overlay
    if (this.game.isPaused) {
      this._drawText("[  P A U S E D  ]", 11, 6, true);
    }

    // Blockade Round Over overlay
    if (this.game.mode === "blockade" && this.game.isRoundOver && !this.game.isGameOver) {
      const p2 = this.game.blockadeOpponent === "cpu" ? "CPU" : "P2";
      const msg = this.game.roundWinner === "tie" ? "[  ROUND TIED!  ]" : (this.game.roundWinner === "p1" ? "[  P1 SCORES!   ]" : `[  ${p2} SCORES!   ]`);
      this._drawText(msg, 11, 6, true);
    }
  }

  _renderGameOverOverlay() {
    if (this.game.mode === "blockade") {
      const p2 = this.game.blockadeOpponent === "cpu" ? "CPU" : "P2";
      const win = this.game.p1Wins >= this.game.matchTarget ? "P1 WINS MATCH!" : `${p2} WINS MATCH!`;
      this._drawText("============================", 6, 3, false);
      this._drawText(`    ${win.padStart(16).padEnd(20)}    `, 6, 4, true);
      this._drawText("============================", 6, 5, false);
      this._drawText(`   FINAL: P1 ${this.game.p1Wins} vs ${p2} ${this.game.p2Wins}   `, 6, 6, false);
      this._drawText(" [Press Any Key / Tap Menu] ", 6, 8, true);
      this._drawText("============================", 6, 9, false);
    } else {
      this._drawText("============================", 6, 3, false);
      this._drawText("      G A M E   O V E R     ", 6, 4, true);
      this._drawText("============================", 6, 5, false);
      this._drawText(`   SCORE:        ${String(this.game.score).padStart(5, "0")}      `, 6, 6, false);
      this._drawText(" [Press Any Key / Tap Menu] ", 6, 8, true);
      this._drawText("============================", 6, 9, false);
    }
  }

  _renderNameEntryOverlay() {
    this._drawText("============================", 6, 3, false);
    this._drawText("    ★ NEW HIGH SCORE! ★     ", 6, 4, true);
    this._drawText("============================", 6, 5, false);
    this._drawText(`        SCORE: ${String(this.game.score).padStart(5, "0")}        `, 6, 6, false);
    this._drawText("       ENTER INITIALS:      ", 6, 7, false);
    this._drawText(`           [ ${this.nameBuffer.padEnd(3)} ]          `, 6, 8, true);
    this._drawText("============================", 6, 9, false);
  }

  _renderHighScores() {
    this._drawText("ıll" + "HIGH SCORES".padStart(20).padEnd(31) + "[■■■■]", 0, 0);
    this._drawText("-".repeat(40), 0, 1);
    for (let i = 0; i < 7 && i < this.highscores.length; i++) {
      const s = this.highscores[i];
      const line = ` ${i + 1}. ${s.name.padEnd(4)}  ${String(s.score).padStart(4, "0")}  L${s.level}`;
      this._drawText(line.padEnd(40), 0, 2 + i, i === 0);
    }
    this._drawText("[Press Any Key / Tap Menu]", 7, 11);
  }

  _renderHelp() {
    this._drawText("ıll" + "INSTRUCTIONS".padStart(21).padEnd(31) + "[■■■■]", 0, 0);
    this._drawText("-".repeat(40), 0, 1);
    const lines = [
      "MODES: Snake 1997, Snake II, Blockade",
      "CONTROLS:",
      "  P1: 2/8/4/6, WASD, Arrows, Swipe",
      "  P2 (Blockade): Arrows / IJKL",
      "  P: Pause   M: Sound   V: View Mode",
      "  T: Theme   Q/Esc: Return to Menu"
    ];
    lines.forEach((l, i) => this._drawText(l.padEnd(40), 0, 2 + i));
    this._drawText("[Press Any Key / Tap Menu]", 7, 11);
  }
}

// Launch app on DOM ready
window.addEventListener("DOMContentLoaded", () => {
  window.app = new NokiaWebApp();
});
