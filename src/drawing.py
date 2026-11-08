"""Referans noktalarını kare üzerine çizen yardımcılar.

Bu modül MediaPipe'a bağımlı değildir: noktalar normalize edilmiş
`(x, y)` çiftleri (0-1 aralığı), bağlantılar `(başlangıç, bitiş)`
indeks çiftleri olarak verilir. Böylece kamera olmadan test edilebilir.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import cv2
import numpy as np

Point = tuple[float, float]
Connection = tuple[int, int]

# BGR renkler
HAND_POINT_COLOR = (0, 0, 255)
HAND_LINE_COLOR = (255, 255, 255)
FACE_LINE_COLOR = (80, 200, 120)
TEXT_COLOR = (255, 255, 255)


def to_pixels(points: Sequence[Point], width: int, height: int) -> list[tuple[int, int]]:
    """Normalize noktaları piksel koordinatlarına çevirir.

    Kare dışına taşan noktalar kenara sabitlenir (clamp).
    """
    pixels = []
    for x, y in points:
        px = min(max(int(round(x * width)), 0), width - 1)
        py = min(max(int(round(y * height)), 0), height - 1)
        pixels.append((px, py))
    return pixels


def draw_landmarks(
    frame: np.ndarray,
    points: Sequence[Point],
    connections: Iterable[Connection] = (),
    point_color: tuple[int, int, int] | None = HAND_POINT_COLOR,
    line_color: tuple[int, int, int] = HAND_LINE_COLOR,
    point_radius: int = 4,
    line_thickness: int = 2,
) -> np.ndarray:
    """Bir el/yüz için noktaları ve bağlantıları `frame` üzerine çizer.

    `point_color=None` verilirse yalnızca çizgiler çizilir (yüz için).
    Kare yerinde değiştirilir ve kolaylık için geri döndürülür.
    """
    height, width = frame.shape[:2]
    pixels = to_pixels(points, width, height)
    for start, end in connections:
        if start < len(pixels) and end < len(pixels):
            cv2.line(frame, pixels[start], pixels[end], line_color, line_thickness, cv2.LINE_AA)
    if point_color is not None:
        for p in pixels:
            cv2.circle(frame, p, point_radius, point_color, -1, cv2.LINE_AA)
    return frame


def draw_hands(frame: np.ndarray, hands: Sequence[Sequence[Point]],
               connections: Iterable[Connection]) -> np.ndarray:
    connections = list(connections)
    for hand in hands:
        draw_landmarks(frame, hand, connections)
    return frame


def draw_faces(frame: np.ndarray, faces: Sequence[Sequence[Point]],
               connections: Iterable[Connection]) -> np.ndarray:
    connections = list(connections)
    for face in faces:
        draw_landmarks(frame, face, connections, point_color=None,
                       line_color=FACE_LINE_COLOR, line_thickness=1)
    return frame


def draw_stats(frame: np.ndarray, hand_count: int, face_count: int, fps: float) -> np.ndarray:
    """Sol üst köşeye el/yüz sayısı ve FPS yazar."""
    text = f"El: {hand_count}  Yuz: {face_count}  FPS: {fps:.1f}"
    cv2.putText(frame, text, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, text, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, TEXT_COLOR, 2, cv2.LINE_AA)
    return frame
