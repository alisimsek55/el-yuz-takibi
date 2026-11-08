import numpy as np

from src import drawing


def blank(h=100, w=200):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_to_pixels_scales_normalized_points():
    assert drawing.to_pixels([(0.0, 0.0), (0.5, 0.5)], 200, 100) == [(0, 0), (100, 50)]


def test_to_pixels_clamps_points_outside_frame():
    assert drawing.to_pixels([(-0.2, 1.5), (1.0, 1.0)], 200, 100) == [(0, 99), (199, 99)]


def test_draw_landmarks_draws_points_and_lines():
    frame = blank()
    drawing.draw_landmarks(frame, [(0.1, 0.5), (0.9, 0.5)], [(0, 1)],
                           point_color=(0, 0, 255), line_color=(255, 255, 255))
    assert tuple(frame[50, 20]) == (0, 0, 255)       # nokta
    assert tuple(frame[50, 100]) == (255, 255, 255)  # çizginin ortası
    assert tuple(frame[10, 10]) == (0, 0, 0)         # dokunulmamış alan


def test_draw_landmarks_ignores_invalid_connection_indices():
    frame = blank()
    drawing.draw_landmarks(frame, [(0.5, 0.5)], [(0, 5)])
    assert frame.any()


def test_draw_faces_without_points_only_draws_lines():
    frame = blank()
    drawing.draw_faces(frame, [[(0.1, 0.2), (0.9, 0.2)]], [(0, 1)])
    assert frame[19:22, 100].any()  # 1 px kenar yumuşatılmış çizgi
    assert not (frame == drawing.HAND_POINT_COLOR).all(axis=2).any()


def test_draw_with_no_detections_leaves_frame_unchanged():
    frame = blank()
    drawing.draw_hands(frame, [], [(0, 1)])
    drawing.draw_faces(frame, [], [(0, 1)])
    assert not frame.any()
