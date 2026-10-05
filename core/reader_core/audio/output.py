import threading
import time

from ..errors import ReaderError


class AudioOutput:
    def __init__(self):
        self.position = 0
        self.lock = threading.Lock()

    def play(
        self,
        audio,
        rate: int,
        cancelled: threading.Event,
        paused: threading.Event,
        volume,
        start_seconds: float = 0,
    ):
        import sounddevice as sd

        self.position = min(len(audio), int(max(0, start_seconds) * rate))
        finished = threading.Event()

        def callback(outdata, frames, timing, status):
            outdata.fill(0)
            if cancelled.is_set():
                raise sd.CallbackStop
            if paused.is_set():
                return
            with self.lock:
                end = min(self.position + frames, len(audio))
                count = end - self.position
                outdata[:count, 0] = audio[self.position : end] * volume()
                self.position = end
                if end >= len(audio):
                    raise sd.CallbackStop

        try:
            with sd.OutputStream(
                samplerate=rate,
                channels=1,
                dtype="float32",
                callback=callback,
                finished_callback=finished.set,
            ):
                while not finished.wait(0.04):
                    if cancelled.is_set():
                        break
        except Exception as exc:
            raise ReaderError(
                "audio_unavailable",
                "No se puede reproducir audio. Comprueba el dispositivo de salida.",
            ) from exc


class SilentOutput(AudioOutput):
    """Only selected explicitly by tests; never a production fallback."""

    def play(self, audio, rate, cancelled, paused, volume, start_seconds=0):
        self.position = int(start_seconds * rate)
        while self.position < len(audio) and not cancelled.is_set():
            if not paused.is_set():
                self.position += max(1, int(rate * 0.01))
            time.sleep(0.01)
