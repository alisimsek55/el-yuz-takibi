"""Tkinter + ttkbootstrap masaüstü arayüzü.

Çalıştırma:
    python -m src.app
"""

from __future__ import annotations

import os

# MediaPipe/TFLite'ın konsola yazdığı bilgi loglarını azalt.
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import threading
import time
import tkinter as tk
import traceback
from dataclasses import dataclass

import cv2
import numpy as np
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from . import drawing
from .camera import Camera, CameraError
from .detector import Tracker
from .fps import FPSCounter
from .models import missing_models

VIEW_W, VIEW_H = 960, 540


@dataclass
class FrameInfo:
    """Arka plan iş parçacığından arayüze aktarılan son kare."""

    image: np.ndarray  # RGB, görüntü alanına sığdırılmış
    hand_count: int
    face_count: int
    fps: float


def fit_to_view(frame: np.ndarray, width: int = VIEW_W, height: int = VIEW_H) -> np.ndarray:
    """Kareyi en-boy oranını koruyarak görüntü alanına sığdırır."""
    h, w = frame.shape[:2]
    scale = min(width / w, height / h)
    if scale == 1:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


class TrackingWorker(threading.Thread):
    """Kamerayı okur, tespit yapar ve son kareyi paylaşır.

    Tespit, arayüz donmasın diye ana iş parçacığı yerine burada yapılır.
    """

    def __init__(self, camera: Camera, tracker: Tracker, settings: dict[str, bool]) -> None:
        super().__init__(daemon=True)
        self.camera = camera
        self.tracker = tracker
        self.settings = settings  # "hands", "faces", "mirror" -> bool
        self.stop_event = threading.Event()
        self.error: str | None = None
        self._latest: FrameInfo | None = None
        self._lock = threading.Lock()

    def latest(self) -> FrameInfo | None:
        """Yeni bir kare varsa döndürür, yoksa None."""
        with self._lock:
            info, self._latest = self._latest, None
        return info

    def run(self) -> None:
        fps = FPSCounter()
        try:
            self.camera.open()
            while not self.stop_event.is_set():
                frame = self.camera.read()
                if self.settings["mirror"]:
                    frame = cv2.flip(frame, 1)
                # Mutlak monoton saat: tracker yeniden başlatmalar arasında
                # paylaşıldığı için oturum başına sıfırlanan sayaç kullanılmaz.
                ts = time.monotonic_ns() // 1_000_000
                det = self.tracker.process(frame, ts, hands=self.settings["hands"],
                                           faces=self.settings["faces"])
                det.draw(frame)
                current_fps = fps.tick()
                drawing.draw_stats(frame, det.hand_count, det.face_count, current_fps)
                rgb = cv2.cvtColor(fit_to_view(frame), cv2.COLOR_BGR2RGB)
                with self._lock:
                    self._latest = FrameInfo(rgb, det.hand_count, det.face_count, current_fps)
        except CameraError as exc:
            self.error = str(exc)
        except Exception as exc:  # MediaPipe/OpenCV hataları arayüzde görünsün
            traceback.print_exc()
            self.error = f"{type(exc).__name__}: {exc}"
        finally:
            self.camera.release()


class App(ttk.Window):
    def __init__(self) -> None:
        super().__init__(title="El ve Yüz Takibi", themename="darkly", minsize=(1240, 620))
        self.tracker: Tracker | None = None
        self.worker: TrackingWorker | None = None
        self._stopping: TrackingWorker | None = None  # durdurulmuş ama henüz bitmemiş iş
        self._stop_message = ""
        self.settings = {"hands": True, "faces": True, "mirror": True}
        self._photo: ImageTk.PhotoImage | None = None

        self.hands_var = tk.BooleanVar(value=True)
        self.faces_var = tk.BooleanVar(value=True)
        self.mirror_var = tk.BooleanVar(value=True)
        self.camera_var = tk.IntVar(value=0)
        self.hand_count_var = tk.StringVar(value="0")
        self.face_count_var = tk.StringVar(value="0")
        self.fps_var = tk.StringVar(value="0.0")
        self.status_var = tk.StringVar(value="Hazır. Başlamak için 'Kamerayı Başlat' düğmesine basın.")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(30, self._refresh)

    # ---------- arayüz ----------
    def _build_ui(self) -> None:
        ttk.Label(self, textvariable=self.status_var, padding=(12, 4),
                  bootstyle="inverse-dark").pack(side="bottom", fill="x")

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        panel = ttk.Frame(root, padding=(16, 0, 0, 0))
        panel.pack(side="right", fill="y")

        self.video = ttk.Label(root, anchor="center", text="Kamera kapalı",
                               font=("Segoe UI", 16), bootstyle="secondary")
        self.video.pack(side="left", fill="both", expand=True)

        ttk.Label(panel, text="Kontroller", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        cam_row = ttk.Frame(panel)
        cam_row.pack(fill="x", pady=(8, 4))
        ttk.Label(cam_row, text="Kamera no:").pack(side="left")
        ttk.Spinbox(cam_row, from_=0, to=9, width=4, textvariable=self.camera_var).pack(side="right")

        self.start_btn = ttk.Button(panel, text="Kamerayı Başlat", bootstyle="success",
                                    command=self.start)
        self.start_btn.pack(fill="x", pady=4)
        self.stop_btn = ttk.Button(panel, text="Durdur", bootstyle="danger",
                                   command=self.stop, state="disabled")
        self.stop_btn.pack(fill="x", pady=4)

        ttk.Separator(panel).pack(fill="x", pady=12)
        for text, var in (("El takibi", self.hands_var), ("Yüz takibi", self.faces_var),
                          ("Ayna görüntü", self.mirror_var)):
            ttk.Checkbutton(panel, text=text, variable=var, bootstyle="round-toggle",
                            command=self._sync_settings).pack(anchor="w", pady=4)

        ttk.Separator(panel).pack(fill="x", pady=12)
        ttk.Label(panel, text="Anlık Durum", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        for label, var, style in (("El sayısı", self.hand_count_var, "info"),
                                  ("Yüz sayısı", self.face_count_var, "success"),
                                  ("FPS", self.fps_var, "warning")):
            row = ttk.Frame(panel)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label).pack(side="left")
            ttk.Label(row, textvariable=var, font=("Segoe UI", 16, "bold"),
                      bootstyle=style).pack(side="right", padx=(24, 0))

    def _sync_settings(self) -> None:
        self.settings["hands"] = self.hands_var.get()
        self.settings["faces"] = self.faces_var.get()
        self.settings["mirror"] = self.mirror_var.get()

    # ---------- kamera kontrolü ----------
    def start(self) -> None:
        if self.worker is not None:
            return
        missing = missing_models()
        if missing:
            self.status_var.set(f"Eksik model: {', '.join(missing)}. Önce 'python -m src.models' çalıştırın.")
            return
        try:
            camera_index = self.camera_var.get()
        except tk.TclError:
            self.status_var.set("Kamera numarası bir tam sayı olmalı.")
            return
        if self.tracker is None:
            self.status_var.set("Modeller yükleniyor...")
            self.update_idletasks()
            try:
                self.tracker = Tracker()
            except Exception as exc:  # bozuk/uyumsuz model dosyası vb.
                self.status_var.set(f"Modeller yüklenemedi: {type(exc).__name__}: {exc}")
                return
        self._sync_settings()
        self.worker = TrackingWorker(Camera(camera_index), self.tracker, self.settings)
        self.worker.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set(f"Kamera {camera_index} açılıyor...")

    def stop(self, message: str = "Kamera durduruldu.") -> None:
        worker = self.worker
        if worker is None:
            return
        worker.stop_event.set()
        worker.join(timeout=2)
        self.worker = None
        self._photo = None
        self.video.configure(image="", text="Kamera kapalı")
        self.hand_count_var.set("0")
        self.face_count_var.set("0")
        self.fps_var.set("0.0")
        self.stop_btn.configure(state="disabled")
        if worker.is_alive():
            # Kamera okuma veya tespit takıldı. İş parçacığı hâlâ kamerayı ve
            # tracker'ı kullanıyor; bitene kadar yeniden başlatmaya izin verme.
            self._stopping = worker
            self._stop_message = message
            self.start_btn.configure(state="disabled")
            self.status_var.set("Kamera kapanıyor, lütfen bekleyin...")
        else:
            self.start_btn.configure(state="normal")
            self.status_var.set(message)

    def _refresh(self) -> None:
        stopping = self._stopping
        if stopping is not None and not stopping.is_alive():
            self._stopping = None
            self.start_btn.configure(state="normal")
            self.status_var.set(self._stop_message)
        worker = self.worker
        if worker is not None:
            if not worker.is_alive():
                self.stop(f"Hata: {worker.error}" if worker.error else "Kamera durdu.")
            else:
                info = worker.latest()
                if info is not None:
                    self._photo = ImageTk.PhotoImage(Image.fromarray(info.image))
                    self.video.configure(image=self._photo, text="")
                    self.hand_count_var.set(str(info.hand_count))
                    self.face_count_var.set(str(info.face_count))
                    self.fps_var.set(f"{info.fps:.1f}")
                    self.status_var.set(f"Kamera {worker.camera.index} çalışıyor.")
        self.after(15, self._refresh)

    def on_close(self) -> None:
        self.stop()
        # Takılı bir iş parçacığı tracker'ı hâlâ kullanıyorsa altından kapatma;
        # süreç kapanırken (daemon thread) kaynaklar zaten bırakılır.
        if self.tracker is not None and self._stopping is None:
            self.tracker.close()
        self.destroy()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
