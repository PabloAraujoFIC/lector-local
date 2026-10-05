import sys
import threading

from ..errors import ReaderError


def system_output_device(sd):
    """Use the session audio server instead of a cached physical ALSA card."""
    if sys.platform == "linux":
        devices = sd.query_devices()
        apis = sd.query_hostapis()
        for name in ("pipewire", "pulse"):
            for index, device in enumerate(devices):
                if (
                    device["name"] == name
                    and device["max_output_channels"] > 0
                    and apis[device["hostapi"]]["name"] == "ALSA"
                ):
                    return index
    return None


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
                device=system_output_device(sd),
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
