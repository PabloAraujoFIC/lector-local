import time

from reader_core.audio.output import AudioOutput


class SilentOutput(AudioOutput):
    """Only selected explicitly by tests; never a production fallback."""

    def play(self, audio, rate, cancelled, paused, volume, start_seconds=0):
        self.position = int(start_seconds * rate)
        while self.position < len(audio) and not cancelled.is_set():
            if not paused.is_set():
                self.position += max(1, int(rate * 0.01))
            time.sleep(0.01)
