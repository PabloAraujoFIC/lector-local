from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class TTSEngine(Protocol):
    identity: str

    def synthesize(
        self, text: str, voice: str, language: str, speed: float, device: str
    ) -> tuple[NDArray[np.float32], int]: ...
