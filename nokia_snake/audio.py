"""
Nokia Monophonic Buzzer Audio Engine.
Emulates the authentic piezoelectric buzzer sound of Nokia phones
using real-time synthesized square waves via ALSA / aplay with
fallback to terminal bell.
"""

import io
import math
import os
import queue
import shutil
import struct
import subprocess
import sys
import threading
import time
import wave
from typing import List, Tuple, Optional

class SoundEngine:
    """Threaded audio engine synthesizing monophonic Nokia tones."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._has_aplay = shutil.which("aplay") is not None
        self._q: queue.Queue = queue.Queue(maxsize=8)
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._cache = {}

        if self._has_aplay:
            self._start_worker()

    def _start_worker(self):
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                raw_wav = self._q.get(timeout=0.2)
            except queue.Empty:
                continue

            if raw_wav is None:
                break

            try:
                # Play through aplay
                subprocess.run(
                    ["aplay", "-q"],
                    input=raw_wav,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0
                )
            except Exception:
                pass
            finally:
                self._q.task_done()

    def _make_square_wav(self, notes: List[Tuple[int, float, int]], sample_rate: int = 22050) -> bytes:
        """
        Generate raw WAV byte stream with Nokia-style square waves.
        notes: list of (frequency_hz, duration_sec, volume)
        """
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            raw_frames = []
            for freq, dur, vol in notes:
                n_samples = int(dur * sample_rate)
                if freq <= 0:
                    # Silence
                    raw_frames.append(b'\x00\x00' * n_samples)
                    continue

                period = sample_rate / freq
                fade_len = min(120, n_samples // 4)
                for i in range(n_samples):
                    # Square wave
                    phase = (i % period) / period
                    sample_val = vol if phase < 0.5 else -vol

                    # Slight fade-out at the end of each note to prevent loud DC clicks
                    if i > n_samples - fade_len:
                        scale = (n_samples - i) / fade_len
                        sample_val = int(sample_val * scale)

                    raw_frames.append(struct.pack('<h', sample_val))

            w.writeframes(b''.join(raw_frames))
        return buf.getvalue()

    def _play_tones(self, notes: List[Tuple[int, float, int]], cache_key: Optional[str] = None):
        if not self.enabled:
            return

        if self._has_aplay:
            if cache_key and cache_key in self._cache:
                raw = self._cache[cache_key]
            else:
                raw = self._make_square_wav(notes)
                if cache_key:
                    self._cache[cache_key] = raw

            try:
                self._q.put_nowait(raw)
            except queue.Full:
                pass
        else:
            # Fallback to terminal bell
            try:
                sys.stdout.write('\a')
                sys.stdout.flush()
            except Exception:
                pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    # --- Game Sound Effects ---

    def play_eat(self):
        """Crisp high-pitch Nokia blip when eating regular food."""
        # 1046 Hz (C6), 55ms
        self._play_tones([(1046, 0.055, 12000)], cache_key="eat")

    def play_bonus(self):
        """Ascending double chirp when eating bonus insect."""
        # 784 Hz (G5) -> 1318 Hz (E6)
        notes = [(784, 0.045, 13000), (1318, 0.070, 14000)]
        self._play_tones(notes, cache_key="bonus")

    def play_crash(self):
        """Classic low pitch buzzer sound on collision / game over."""
        # Rapid descending buzz 220Hz -> 146Hz -> 90Hz
        notes = [
            (220, 0.08, 14000),
            (160, 0.10, 14000),
            (95, 0.22, 15000),
        ]
        self._play_tones(notes, cache_key="crash")

    def play_highscore(self):
        """Triumphant Nokia victory fanfare for new high score."""
        notes = [
            (659, 0.08, 12000),  # E5
            (830, 0.08, 12000),  # G#5
            (987, 0.08, 12000),  # B5
            (1318, 0.25, 14000), # E6
        ]
        self._play_tones(notes, cache_key="highscore")

    def play_click(self):
        """Key tick for menu navigation and turning."""
        self._play_tones([(2200, 0.015, 8000)], cache_key="click")

    def play_nokia_tune(self):
        """The world-famous Nokia Ringtone (Gran Vals by Francisco Tárrega)."""
        # E5, D5, F#4, G#4, C#5, B4, D4, E4, B4, A4, C#4, E4, A4
        melody = [
            (659, 0.11, 12000),  # E5
            (587, 0.11, 12000),  # D5
            (370, 0.20, 12000),  # F#4
            (415, 0.20, 12000),  # G#4
            (554, 0.11, 12000),  # C#5
            (494, 0.11, 12000),  # B4
            (294, 0.20, 12000),  # D4
            (330, 0.20, 12000),  # E4
            (494, 0.11, 12000),  # B4
            (440, 0.11, 12000),  # A4
            (277, 0.20, 12000),  # C#4
            (330, 0.20, 12000),  # E4
            (440, 0.40, 13000),  # A4
        ]
        self._play_tones(melody, cache_key="nokia_tune")

    def shutdown(self):
        self._stop_event.set()
        try:
            self._q.put_nowait(None)
        except Exception:
            pass
