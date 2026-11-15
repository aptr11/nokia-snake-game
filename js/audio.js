/**
 * Nokia Sound Synthesizer via Web Audio API.
 * Emulates the 8-bit monophonic square-wave buzzer.
 */

class WebSoundEngine {
  constructor() {
    this.enabled = true;
    this.ctx = null;
  }

  _initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    return this.enabled;
  }

  _playToneSequence(notes) {
    if (!this.enabled) return;
    this._initContext();
    if (!this.ctx) return;

    let startTime = this.ctx.currentTime;
    for (const [freq, dur] of notes) {
      if (freq <= 0) {
        startTime += dur;
        continue;
      }
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(freq, startTime);

      // Volume envelope with gentle decay
      gain.gain.setValueAtTime(0.12, startTime);
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + dur);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(startTime);
      osc.stop(startTime + dur);

      startTime += dur;
    }
  }

  playEat() {
    this._playToneSequence([[1046, 0.055]]);
  }

  playBonus() {
    this._playToneSequence([[784, 0.045], [1318, 0.070]]);
  }

  playCrash() {
    this._playToneSequence([[220, 0.08], [160, 0.10], [95, 0.22]]);
  }

  playHighScore() {
    this._playToneSequence([[659, 0.08], [830, 0.08], [987, 0.08], [1318, 0.25]]);
  }

  playClick() {
    this._playToneSequence([[2200, 0.015]]);
  }

  playNokiaTune() {
    const melody = [
      [659, 0.11], [587, 0.11], [370, 0.20], [415, 0.20],
      [554, 0.11], [494, 0.11], [294, 0.20], [330, 0.20],
      [494, 0.11], [440, 0.11], [277, 0.20], [330, 0.20],
      [440, 0.40]
    ];
    this._playToneSequence(melody);
  }
}
