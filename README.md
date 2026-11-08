# Kamera Tabanlı El ve Yüz Takibi

Python, OpenCV ve MediaPipe ile web kamerasından **gerçek zamanlı el ve yüz referans noktası (landmark) takibi** yapan masaüstü uygulaması. Arayüz Tkinter + ttkbootstrap ile yazılmıştır.

> **English summary:** A desktop app that tracks hand and face landmarks from a webcam in real time using OpenCV and the MediaPipe Tasks API (HandLandmarker + FaceLandmarker). The ttkbootstrap GUI lets you start/stop the camera, toggle hand and face tracking independently, and shows live hand/face counts and FPS. Detection runs on a background thread so the UI stays responsive. Setup: create a venv, `pip install -r requirements.txt`, `python -m src.models` to download the models, then `python -m src.app`.

![Ekran görüntüsü](docs/ekran-goruntusu.png)
<!-- Ekran görüntüsünü docs/ekran-goruntusu.png olarak ekleyin. -->

## Özellikler

- OpenCV ile kamera akışı (Windows'ta hızlı açılış için DirectShow)
- MediaPipe **HandLandmarker** ile 2 ele kadar 21 noktalı el iskeleti
- MediaPipe **FaceLandmarker** ile 478 noktalı yüz ağından kontur ve iris çizimi
- El ve yüz takibini **ayrı ayrı** açıp kapatma, ayna görüntü seçeneği
- Anlık **el sayısı, yüz sayısı ve FPS** göstergesi
- Tespit arka plan iş parçacığında çalışır; arayüz donmaz
- Kamerasız çalışabilen pytest testleri (çizim, sayım, FPS mantığı)

## Gereksinimler

- Python 3.13 (3.10+ ile de çalışması beklenir)
- Bir web kamerası
- Windows 10/11 üzerinde denenmiştir

## Kurulum

```bash
git clone https://github.com/alisimsek55/el-yuz-takibi.git
cd el-yuz-takibi
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Model dosyalarını indirme

MediaPipe Tasks API, `.task` uzantılı model dosyalarına ihtiyaç duyar. Bu dosyalar (~11 MB) depoya eklenmez; `models/` klasörüne şu komutla indirilir:

```bash
python -m src.models
```

Komut, Google'ın resmi MediaPipe model deposundan iki dosyayı indirir:

| Dosya | Kaynak |
|---|---|
| `models/hand_landmarker.task` | https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task |
| `models/face_landmarker.task` | https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task |

İsterseniz bu bağlantılardan elle indirip `models/` klasörüne de koyabilirsiniz.

## Çalıştırma

```bash
python -m src.app
```

1. Gerekirse **Kamera no** değerini değiştirin (dahili kamera genellikle `0`).
2. **Kamerayı Başlat**'a basın.
3. **El takibi** / **Yüz takibi** anahtarlarıyla tespitleri açıp kapatın.
4. Sağ paneldeki sayaçlardan el/yüz sayısını ve FPS'i izleyin.

## Testler

```bash
python -m pytest
```

Testler kamera ya da model dosyası gerektirmez; çizim, nokta dönüştürme, sayım ve FPS hesaplama mantığını doğrular.

## Mimari

```
src/
├── app.py        # ttkbootstrap arayüzü + TrackingWorker (arka plan iş parçacığı)
├── camera.py     # cv2.VideoCapture sarmalayıcısı
├── detector.py   # MediaPipe HandLandmarker/FaceLandmarker -> Detections
├── drawing.py    # MediaPipe'tan bağımsız çizim yardımcıları
├── fps.py        # Kayan pencereli FPS ölçer
└── models.py     # Model dosya yolları ve indirme komutu
tests/            # pytest testleri
```

Veri akışı:

```
Camera.read() ──► Tracker.process() ──► Detections.draw() ──► FPSCounter.tick()
   (BGR kare)      (MediaPipe, VIDEO modu)   (OpenCV çizimi)         │
                                                                     ▼
                                     App._refresh() ◄── TrackingWorker.latest()
                                     (Tkinter, ~60 Hz)   (kilitli son kare)
```

- `detector.py` MediaPipe sonuçlarını sade `(x, y)` listelerine çevirir; böylece `drawing.py` ve testler MediaPipe'a bağımlı kalmaz.
- MediaPipe'ın yeni sürümlerinde eski `mp.solutions` API'si bulunmadığı için **Tasks API** kullanılmıştır.
- Kamera okuma ve tespit `TrackingWorker` iş parçacığında, görüntünün ekrana basılması Tkinter ana döngüsünde (`after`) yapılır.

## Lisans

[MIT](LICENSE)
