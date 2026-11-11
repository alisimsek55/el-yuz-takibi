import numpy as np
import pytest

from src import detector
from src.app import TrackingWorker
from src.camera import CameraError
from src.detector import Detections, Tracker

SETTINGS = {"hands": True, "faces": True, "mirror": False}


class FakeCamera:
    """`frames` kare verir; sonra worker'ı durdurur."""

    index = 0

    def __init__(self, frames=1, fail=None):
        self.frames = frames
        self.fail = fail
        self.worker = None
        self.released = False

    def open(self):
        if self.fail:
            raise self.fail

    def read(self):
        self.frames -= 1
        if self.frames <= 0:
            self.worker.stop_event.set()
        return np.zeros((48, 64, 3), dtype=np.uint8)

    def release(self):
        self.released = True


class RecordingTracker:
    def __init__(self, error=None):
        self.error = error
        self.timestamps = []

    def process(self, frame, ts, hands=True, faces=True):
        if self.error:
            raise self.error
        self.timestamps.append(ts)
        return Detections()


def run_worker(camera, tracker):
    worker = TrackingWorker(camera, tracker, SETTINGS)
    camera.worker = worker
    worker.run()  # thread başlatmadan senkron çalıştır
    return worker


def test_worker_reports_unexpected_errors_and_releases_camera():
    camera = FakeCamera()
    worker = run_worker(camera, RecordingTracker(error=RuntimeError("model çöktü")))
    assert worker.error == "RuntimeError: model çöktü"
    assert camera.released


def test_worker_reports_camera_errors():
    camera = FakeCamera(fail=CameraError("Kamera açılamadı (indeks 0)."))
    worker = run_worker(camera, RecordingTracker())
    assert worker.error == "Kamera açılamadı (indeks 0)."
    assert camera.released


def test_timestamps_keep_increasing_across_restarts():
    tracker = RecordingTracker()
    run_worker(FakeCamera(frames=3), tracker)
    first_session_last = tracker.timestamps[-1]
    run_worker(FakeCamera(frames=1), tracker)
    # Yeni oturum sıfırdan başlamamalı; önceki oturumun saatinden devam etmeli.
    assert tracker.timestamps[-1] >= first_session_last
    assert tracker.timestamps[-1] > 1000


def test_tracker_closes_hand_model_if_face_model_fails(tmp_path, monkeypatch):
    hand_file, face_file = tmp_path / "hand.task", tmp_path / "face.task"
    hand_file.write_bytes(b"x")
    face_file.write_bytes(b"x")

    class FakeHands:
        closed = False

        def close(self):
            self.closed = True

    hands = FakeHands()

    def broken_face_model(options):
        raise RuntimeError("bozuk model")

    monkeypatch.setattr(detector.vision.HandLandmarker, "create_from_options",
                        lambda options: hands)
    monkeypatch.setattr(detector.vision.FaceLandmarker, "create_from_options",
                        broken_face_model)
    with pytest.raises(RuntimeError, match="bozuk model"):
        Tracker(hand_model=hand_file, face_model=face_file)
    assert hands.closed
