# 🗑️ Smart Waste Sorting System

> Real-time AI-powered waste detection and automatic sorting using YOLOv8 and Arduino servo control.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=flat-square)
![ESP32](https://img.shields.io/badge/ESP32-Compatible-red?style=flat-square&logo=espressif)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)

---

## 📌 Overview

The **Smart Waste Sorting System** is a computer vision pipeline that classifies waste in real-time using a YOLOv8 model and automatically directs it to the correct bin via a servo motor controlled by an Arduino board. Designed for embedded deployment with a standard USB webcam and minimal hardware.

---

## ✨ Features

- 🎯 **High Accuracy** — 85%+ detection accuracy on plastic & cardboard
- ⚡ **Real-Time Processing** — 20–30 FPS on a standard webcam
- 🔧 **Automated Sorting** — Servo motor physically redirects waste based on classification
- 🧩 **Modular Design** — Independent training and inference scripts
- 🔌 **ESP32 Compatible** — Uses `ESP32Servo.h` for precise PWM servo control
- 🖥️ **Easy Setup** — Single command to launch the full pipeline

---

## 🛠️ Hardware Requirements

| Component | Specification |
|---|---|
| Camera | USB Webcam (640×480 minimum) |
| Microcontroller | ESP32 (38-pin or DevKit) |
| Servo Motor | SG90 or equivalent (5V) |
| Power Supply | 5V (dedicated for servo) |
| Cables | USB + jumper wires |

### Wiring

```
Servo Motor:
  Signal (Orange) → ESP32 GPIO 18 (or any PWM-capable pin)
  VCC    (Red)    → ESP32 VIN / External 5V
  GND    (Brown)  → ESP32 GND (common ground)

USB Camera → Computer USB Port
ESP32     → Computer USB Port (Serial communication)
```

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/biney17/smart-waste-sorter.git
cd smart-waste-sorter
```

### 2. Install Python dependencies

```bash
pip install ultralytics opencv-python pyserial matplotlib
```

### 3. Extract the dataset

```bash
unzip waste_dataset.zip
```

### 4. Upload Arduino firmware

```
1. Open Arduino IDE
2. Install ESP32 board support:
   File → Preferences → Additional Board Manager URLs:
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
3. Tools → Board → ESP32 Dev Module (or your variant)
4. Install ESP32Servo library: Sketch → Include Library → Manage Libraries → search "ESP32Servo"
5. Tools → Port → Select the correct COM port
6. Open servo_controller.ino
7. Upload with Ctrl+U
```

---

## 🚀 Usage

###  — Run with pre-trained model

```bash
python main.py
```

**Keyboard Controls:**

| Key | Action |
|---|---|
| `Q` | Quit |
| `D` | Toggle debug mode |

---

## ⚙️ Configuration

### Servo angles

Edit `main.py`:

```python
self.servo_angles = {
    0: 22,   # Plastic  → 22°
    1: 140    # Cardboard → 140°
}
```

### Camera index

```python
sorter.run_camera(camera_index=0)  # Change to 1 if you have multiple cameras
```

### Detection confidence threshold

```python
sorter.run_camera(confidence=0.5)  # Increase to 0.7–0.8 for stricter detection
```

---

## 📊 Performance

| Metric | Value |
|---|---|
| mAP50 | ~82% |
| mAP50-95 | ~56% |
| Processing Speed | 20–30 FPS |
| Inference Time | < 100 ms / frame |
| Plastic Accuracy | 85%+ |
| Cardboard Accuracy | 80%+ |

---

## 📁 Project Structure

```
smart-waste-sorter/
│
├── waste_dataset/              # Annotated training data 
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── val/
│   │   ├── images/
│   │   └── labels/
│   └── data.yaml
│
├── main.py
├── servo_controller.ino        # Arduino firmware
├── requirements.txt
└── README.md
```

---

## 🔄 How It Works

```
1. Webcam captures frame at ~30 FPS
         ↓
2. YOLOv8 detects and classifies waste (plastic / cardboard)
         ↓
3. Confidence threshold applied
         ↓
4. Servo angle selected based on class (30° or 90°)
         ↓
5. Angle sent to Arduino via USB Serial
         ↓
6. Servo motor rotates and physically sorts the waste
```

---

## 🔍 Troubleshooting

**Servo not moving**
- Verify ESP32 firmware is uploaded correctly
- Check the correct COM port is selected
- Power the servo with **external 5V** — ESP32's onboard 3.3V is insufficient for most servos
- Ensure common GND between ESP32 and servo power supply
- Confirm you are using a **PWM-capable GPIO** (e.g. GPIO 18, 19, 21, 22)
- Try re-uploading `servo_controller.ino`

**Camera not detected**

```python
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: available")
        cap.release()
```

**Low detection accuracy**
- Improve lighting in the detection area
- Increase training epochs
- Add more labeled training images
- Raise confidence threshold to reduce false positives

---

## 💡 Best Practices

- Place items **~30 cm** from the camera
- Ensure **consistent, diffused lighting** (avoid shadows)
- Keep the camera lens **clean**
- Position items in the **center of the frame**
- Install **CP210x or CH340 drivers** depending on your ESP32 board variant

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## 👩‍💻 Author

**Isra Brahimi** — Embedded Systems & Computer Vision Engineer  
🔗 [GitHub](https://github.com/biney17) · [LinkedIn](https://linkedin.com/in/isra-brahimi) · [Portfolio](https://portfolio-omega-peach-74.vercel.app)