import pytest

from src.fps import FPSCounter


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_fps_is_zero_before_two_frames():
    counter = FPSCounter(clock=FakeClock())
    assert counter.fps == 0.0
    assert counter.tick() == 0.0


def test_fps_at_constant_rate():
    clock = FakeClock()
    counter = FPSCounter(window=10, clock=clock)
    for _ in range(20):
        counter.tick()
        clock.now += 1 / 25
    assert counter.fps == pytest.approx(25.0)


def test_window_tracks_recent_rate_change():
    clock = FakeClock()
    counter = FPSCounter(window=5, clock=clock)
    for step in [0.1] * 10 + [0.02] * 10:
        counter.tick()
        clock.now += step
    assert counter.fps == pytest.approx(50.0)


def test_reset_and_invalid_window():
    counter = FPSCounter(clock=FakeClock())
    counter.tick()
    counter.reset()
    assert counter.fps == 0.0
    with pytest.raises(ValueError):
        FPSCounter(window=1)
