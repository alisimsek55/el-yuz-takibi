from types import SimpleNamespace

import numpy as np

from src.detector import FACE_CONNECTIONS, HAND_CONNECTIONS, Detections, landmarks_to_points


def lm(x, y):
    return SimpleNamespace(x=x, y=y, z=0.0)


def test_counts_follow_detected_items():
    det = Detections(hands=[[(0.1, 0.1)] * 21] * 2, faces=[[(0.5, 0.5)] * 478])
    assert det.hand_count == 2
    assert det.face_count == 1


def test_empty_detections_have_zero_counts():
    det = Detections()
    assert (det.hand_count, det.face_count) == (0, 0)


def test_landmarks_to_points_converts_mediapipe_like_objects():
    result = landmarks_to_points([[lm(0.1, 0.2), lm(0.3, 0.4)], [lm(0.5, 0.6)]])
    assert result == [[(0.1, 0.2), (0.3, 0.4)], [(0.5, 0.6)]]


def test_connections_are_index_pairs_within_model_sizes():
    assert len(HAND_CONNECTIONS) == 21
    assert all(0 <= a < 21 and 0 <= b < 21 for a, b in HAND_CONNECTIONS)
    assert all(0 <= a < 478 and 0 <= b < 478 for a, b in FACE_CONNECTIONS)


def test_draw_marks_frame_when_hand_present():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    hand = [(0.2 + 0.03 * i, 0.5) for i in range(21)]
    Detections(hands=[hand]).draw(frame)
    assert frame.any()
