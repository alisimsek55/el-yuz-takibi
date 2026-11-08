"""MediaPipe model dosyalarının konumu ve indirilmesi.

Komut satırından çalıştırma:
    python -m src.models
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

MODEL_URLS = {
    "hand_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/latest/hand_landmarker.task"
    ),
    "face_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
        "face_landmarker/float16/latest/face_landmarker.task"
    ),
}

HAND_MODEL = MODELS_DIR / "hand_landmarker.task"
FACE_MODEL = MODELS_DIR / "face_landmarker.task"


def missing_models(models_dir: Path = MODELS_DIR) -> list[str]:
    """Klasörde bulunmayan model dosyalarının adlarını döndürür."""
    return [name for name in MODEL_URLS if not (models_dir / name).is_file()]


def download_models(models_dir: Path = MODELS_DIR, force: bool = False) -> None:
    """Eksik model dosyalarını Google'ın resmi deposundan indirir."""
    models_dir.mkdir(parents=True, exist_ok=True)
    for name, url in MODEL_URLS.items():
        target = models_dir / name
        if target.is_file() and not force:
            print(f"[var]     {name}")
            continue
        print(f"[iniyor]  {name} ...", flush=True)
        tmp = target.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(target)
        print(f"[tamam]   {name} ({target.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    download_models(force="--force" in sys.argv)
