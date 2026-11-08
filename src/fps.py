"""Kayan pencereli FPS ölçer."""

from __future__ import annotations

import time
from collections import deque
from typing import Callable


class FPSCounter:
    """Son `window` karenin zaman damgalarından FPS hesaplar.

    `clock` parametresi testlerde sahte zaman vermek için kullanılır.
    """

    def __init__(self, window: int = 30, clock: Callable[[], float] = time.perf_counter) -> None:
        if window < 2:
            raise ValueError("window en az 2 olmalı")
        self._times: deque[float] = deque(maxlen=window)
        self._clock = clock

    def tick(self) -> float:
        """Yeni bir kare kaydeder ve güncel FPS değerini döndürür."""
        self._times.append(self._clock())
        return self.fps

    @property
    def fps(self) -> float:
        if len(self._times) < 2:
            return 0.0
        elapsed = self._times[-1] - self._times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._times) - 1) / elapsed

    def reset(self) -> None:
        self._times.clear()
