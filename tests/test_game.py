"""
Automated unit tests for Nokia Snake.
Tests game mechanics, physics, scoring, input buffering, mazes, and high scores.
"""

import os
import sys
import tempfile
import unittest

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nokia_snake.config import (
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    MODE_SNAKE1, MODE_SNAKE2, GRID_WIDTH, GRID_HEIGHT,
    LEVEL_DELAYS
)
from nokia_snake.game import SnakeGame
from nokia_snake.audio import SoundEngine
from nokia_snake.highscores import HighScoreManager
from nokia_snake.mazes import get_mazes

class DummySoundEngine(SoundEngine):
    """Silent sound engine for testing."""
    def __init__(self):
        super().__init__(enabled=False)
        self.played = []

    def play_eat(self):
        self.played.append("eat")

    def play_bonus(self):
        self.played.append("bonus")

    def play_crash(self):
        self.played.append("crash")

    def play_highscore(self):
        self.played.append("highscore")

    def play_click(self):
        self.played.append("click")

class TestSnakeGame(unittest.TestCase):
    def setUp(self):
        self.sound = DummySoundEngine()
        self.game = SnakeGame(self.sound)

    def test_initial_state(self):
        self.assertEqual(len(self.game.snake), 3)
        self.assertEqual(self.game.direction, DIR_RIGHT)
        self.assertTrue(self.game.is_alive)
        self.assertFalse(self.game.is_paused)
        self.assertFalse(self.game.is_game_over)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.foods_eaten, 0)

    def test_movement_forward(self):
        initial_head = self.game.snake[0]
        # Force a tick
        self.game.last_tick_time = 0
        self.game.update()
        new_head = self.game.snake[0]
        self.assertEqual(new_head, (initial_head[0] + 1, initial_head[1]))
        self.assertEqual(len(self.game.snake), 3)

    def test_input_buffering_and_no_reversal(self):
        # Moving RIGHT initially. Trying to queue LEFT should be ignored
        self.game.queue_direction(DIR_LEFT)
        self.assertEqual(len(self.game.input_queue), 0)

        # Turning UP should be accepted
        self.game.queue_direction(DIR_UP)
        self.assertEqual(len(self.game.input_queue), 1)

        # While queued UP, turning LEFT should be accepted (perpendicular to UP)
        self.game.queue_direction(DIR_LEFT)
        self.assertEqual(len(self.game.input_queue), 2)

        # While queued LEFT, turning RIGHT should be rejected (opposite to LEFT)
        self.game.queue_direction(DIR_RIGHT)
        self.assertEqual(len(self.game.input_queue), 2)

    def test_food_consumption_and_scoring(self):
        self.game.level = 5
        head_x, head_y = self.game.snake[0]
        # Place food right in front of snake
        self.game.food = (head_x + 1, head_y)

        # Step forward
        self.game.last_tick_time = 0
        self.game.update()

        # Snake should have grown to 4 segments
        self.assertEqual(len(self.game.snake), 4)
        # Score should increase by level
        self.assertEqual(self.game.score, 5)
        self.assertEqual(self.game.foods_eaten, 1)
        self.assertIn("eat", self.sound.played)

    def test_wall_collision_snake1(self):
        # Snake 1: Solid border wall
        self.game.set_mode(MODE_SNAKE1)
        # Place snake near right border
        self.game.snake = [(GRID_WIDTH - 1, 5), (GRID_WIDTH - 2, 5), (GRID_WIDTH - 3, 5)]
        self.game.direction = DIR_RIGHT

        # Step into right wall
        self.game.last_tick_time = 0
        self.game.update()

        self.assertFalse(self.game.is_alive)
        self.assertTrue(self.game.is_game_over)
        self.assertEqual(self.game.crash_reason, "wall")
        self.assertIn("crash", self.sound.played)

    def test_edge_wraparound_snake2(self):
        # Snake 2: Edge wraparound
        self.game.set_mode(MODE_SNAKE2)
        self.game.set_maze("snake2_wrap")
        # Place snake at right border
        self.game.snake = [(GRID_WIDTH - 1, 5), (GRID_WIDTH - 2, 5), (GRID_WIDTH - 3, 5)]
        self.game.direction = DIR_RIGHT

        # Step into right wall: should wrap to left edge (x=0)
        self.game.last_tick_time = 0
        self.game.update()

        self.assertTrue(self.game.is_alive)
        self.assertEqual(self.game.snake[0], (0, 5))

    def test_self_collision(self):
        # Create a loop: head crashes into neck/body
        # Head at (5, 5), moving left into (4, 5)
        self.game.snake = [
            (5, 5), (5, 6), (4, 6), (4, 5), (4, 4)
        ]
        self.game.direction = DIR_LEFT
        self.game.last_tick_time = 0
        self.game.update()

        self.assertFalse(self.game.is_alive)
        self.assertTrue(self.game.is_game_over)
        self.assertEqual(self.game.crash_reason, "self")

    def test_bonus_bug_lifecycle(self):
        self.game.set_mode(MODE_SNAKE2)
        self.game.spawn_bonus()
        self.assertIsNotNone(self.game.bonus_bug)
        self.assertGreater(self.game.bonus_timer, 0)

        # Place head directly on bonus bug
        head_x, head_y = self.game.snake[0]
        self.game.bonus_bug = (head_x + 1, head_y)
        initial_score = self.game.score

        self.game.last_tick_time = 0
        self.game.update()

        # Bonus should be consumed and awarded
        self.assertIsNone(self.game.bonus_bug)
        self.assertGreater(self.game.score, initial_score)
        self.assertIn("bonus", self.sound.played)

class TestHighScores(unittest.TestCase):
    def test_persistence_and_ranking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = HighScoreManager(config_dir=tmpdir)
            top = mgr.get_top()
            self.assertGreater(len(top), 0)

            # Add high score
            rank = mgr.add_score("TST", 9999, 9, "Classic 1997")
            self.assertEqual(rank, 1)

            # Reload manager from same directory
            mgr2 = HighScoreManager(config_dir=tmpdir)
            top2 = mgr2.get_top()
            self.assertEqual(top2[0]["name"], "TST")
            self.assertEqual(top2[0]["score"], 9999)

class TestAudioWaveGeneration(unittest.TestCase):
    def test_wave_synthesis(self):
        se = SoundEngine(enabled=False)
        wav_data = se._make_square_wav([(440, 0.05, 10000)])
        self.assertGreater(len(wav_data), 100)
        # Check WAV header
        self.assertTrue(wav_data.startswith(b"RIFF"))

if __name__ == "__main__":
    unittest.main()
