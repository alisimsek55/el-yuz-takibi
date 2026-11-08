"""MediaPipe Tasks API ile el ve yüz referans noktası tespiti.

MediaPipe 0.10.x sonrası sürümlerde eski `mp.solutions` API'si
kaldırıldığı için `HandLandmarker` ve `FaceLandmarker` kullanılır.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from . import drawing
from .models import FACE_MODEL, HAND_MODEL

HAND_CONNECTIONS: list[drawing.Connection] = [
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
]
# Tam ağ (tesselation) yerine kontur + iris: daha okunaklı ve hızlı.
FACE_CONNECTIONS: list[drawing.Connection] = [
    (c.start, c.end)
    for c in (
        vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS
        + vision.FaceLandmarksConnections.FACE_LANDMARKS_LEFT_IRIS
        + vision.FaceLandmarksConnections.FACE_LANDMARKS_RIGHT_IRIS
    )
]


@dataclass
class Detections:
    """Bir karedeki tespitler; her el/yüz normalize `(x, y)` listesidir."""

    hands: list[list[drawing.Point]] = field(default_factory=list)
    faces: list[list[drawing.Point]] = field(default_factory=list)

    @property
    def hand_count(self) -> int:
        return len(self.hands)

    @property
    def face_count(self) -> int:
        return len(self.faces)

    def draw(self, frame: np.ndarray) -> np.ndarray:
        drawing.draw_faces(frame, self.faces, FACE_CONNECTIONS)
        drawing.draw_hands(frame, self.hands, HAND_CONNECTIONS)
        return frame


def landmarks_to_points(landmark_lists) -> list[list[drawing.Point]]:
    """MediaPipe `NormalizedLandmark` listelerini sade `(x, y)` listelerine çevirir."""
    return [[(lm.x, lm.y) for lm in landmarks] for landmarks in landmark_lists]


class Tracker:
    """El ve yüz landmarker'larını VIDEO modunda çalıştırır."""

    def __init__(self, max_hands: int = 2, max_faces: int = 2,
                 hand_model: Path = HAND_MODEL, face_model: Path = FACE_MODEL) -> None:
        missing = [p.name for p in (hand_model, face_model) if not p.is_file()]
        if missing:
            raise FileNotFoundError(
                f"Model dosyası bulunamadı: {', '.join(missing)}. "
                "Önce `python -m src.models` komutunu çalıştırın."
            )
        mode = vision.RunningMode.VIDEO
        self._hands = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(hand_model)),
                running_mode=mode,
                num_hands=max_hands,
            )
        )
        self._faces = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(face_model)),
                running_mode=mode,
                num_faces=max_faces,
            )
        )
        self._last_ts = -1

    def process(self, frame_bgr: np.ndarray, timestamp_ms: int,
                hands: bool = True, faces: bool = True) -> Detections:
        """Bir BGR karede seçili tespitleri çalıştırır."""
        result = Detections()
        if not (hands or faces):
            return result
        # VIDEO modu kesin artan zaman damgası ister.
        timestamp_ms = max(timestamp_ms, self._last_ts + 1)
        self._last_ts = timestamp_ms

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        if hands:
            result.hands = landmarks_to_points(
                self._hands.detect_for_video(image, timestamp_ms).hand_landmarks)
        if faces:
            result.faces = landmarks_to_points(
                self._faces.detect_for_video(image, timestamp_ms).face_landmarks)
        return result

    def close(self) -> None:
        self._hands.close()
        self._faces.close()

    def __enter__(self) -> "Tracker":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

