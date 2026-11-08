"""OpenCV ile kamera erişimi."""

from __future__ import annotations

import sys

import cv2
import numpy as np


class CameraError(RuntimeError):
    """Kamera açılamadığında veya kare okunamadığında fırlatılır."""


class Camera:
    """`cv2.VideoCapture` için küçük bir sarmalayıcı.

    `with Camera(0) as cam:` şeklinde kullanılabilir.
    """

    def __init__(self, index: int = 0, width: int = 1280, height: int = 720) -> None:
        self.index = index
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def open(self) -> None:
        if self.is_open:
            return
        # Windows'ta DirectShow arka ucu kamerayı çok daha hızlı açar.
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        cap = cv2.VideoCapture(self.index, backend)
        if not cap.isOpened():
            cap.release()
            raise CameraError(f"Kamera açılamadı (indeks {self.index}).")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap = cap

    def read(self) -> np.ndarray:
        """Bir BGR kare döndürür."""
        if not self.is_open:
            raise CameraError("Kamera açık değil.")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise CameraError("Kameradan kare okunamadı.")
        return frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.release()
