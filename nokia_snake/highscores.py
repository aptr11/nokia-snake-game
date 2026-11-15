"""
High score tracking and persistence for Nokia Snake.
Stores scores in ~/.config/nokia_snake/highscores.json.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional

DEFAULT_SCORES = [
    {"name": "TNA", "score": 500, "level": 9, "mode": "Classic 1997", "date": "1997-12-01"},
    {"name": "NOK", "score": 331, "level": 7, "mode": "Classic 1997", "date": "2000-09-01"},
    {"name": "SNK", "score": 240, "level": 5, "mode": "Classic 1997", "date": "2001-03-15"},
    {"name": "331", "score": 180, "level": 4, "mode": "Snake II",     "date": "2001-08-20"},
    {"name": "RET", "score": 120, "level": 3, "mode": "Classic 1997", "date": "2002-05-10"},
]

class HighScoreManager:
    """Manages persistent high scores and personal bests."""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.config/nokia_snake")
        self.config_dir = config_dir
        self.file_path = os.path.join(self.config_dir, "highscores.json")
        self.scores: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.scores = data
                        return
        except Exception:
            pass
        self.scores = list(DEFAULT_SCORES)
        self._save()

    def _save(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except Exception:
            pass

    def get_top(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_scores = sorted(self.scores, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_scores[:limit]

    def get_highest_score(self) -> int:
        if not self.scores:
            return 0
        return max(s.get("score", 0) for s in self.scores)

    def is_high_score(self, score: int) -> bool:
        if score <= 0:
            return False
        top = self.get_top(10)
        if len(top) < 10:
            return True
        return score > top[-1].get("score", 0)

    def add_score(self, name: str, score: int, level: int, mode: str) -> int:
        """Add new score and return 1-based rank."""
        clean_name = (name.strip().upper()[:5] or "YOU")
        date_str = time.strftime("%Y-%m-%d")
        entry = {
            "name": clean_name,
            "score": score,
            "level": level,
            "mode": mode,
            "date": date_str,
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.scores = self.scores[:20]  # Keep top 20
        self._save()

        for idx, s in enumerate(self.scores):
            if s is entry:
                return idx + 1
        return len(self.scores)
