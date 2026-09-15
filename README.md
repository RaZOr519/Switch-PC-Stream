# 🎮 SwitchLite-PC-Stream

> **Low-Latency PC Game Streaming on a Completely Stock, Unmodded Nintendo Switch Lite**
> *Render 720p @ 60 FPS over local network using the Switch's hidden captive-portal WebKit browser!*

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)
![Resolution](https://img.shields.io/badge/Resolution-1280x720%20%40%2060FPS-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Nintendo%20Switch%20Lite%20%28Stock%2FUnmodded%29-red.svg)

---

## 🎥 Real-World Video Demonstrations

Check out live video test runs of the Nintendo Switch Lite streaming at 720p @ 60 FPS over local network:

https://github.com/user-attachments/assets/demo1.mp4

https://github.com/user-attachments/assets/demo2.mp4

> *Note: Videos are hosted in the [`media/`](media/) folder (`media/demo1.mp4` and `media/demo2.mp4`).*

---

## 🌟 Overview

**SwitchLite-PC-Stream** is a high-performance open-source game streaming solution for the Nintendo Switch Lite **without modchips, jailbreaks, Android/Linux installations, or custom firmware**.

By leveraging the Switch's hidden WebKit browser (accessible via SwitchBru DNS), this project establishes a binary WebSocket stream using optimized JPEG frame compression and DXCAM GPU capture. Switch physical inputs (Analog Sticks, D-Pad, Buttons) are transmitted back to the PC over WebSocket and injected directly into Windows as **Native Xbox 360 Controller (XInput)** and **Keyboard/Mouse** events.

---

## 🚀 Key Features

* **⚡ Ultra-Fast DXCAM GPU Capture**: Uses Windows DirectX 11 Desktop Duplication API (`dxcam`) for **0.53 ms capture latency (1,899 FPS capability)**.
* **🎯 720p @ 60 FPS Real-Time Streaming**: Native 1280x720 resolution tailored for the Switch Lite display with minimal latency (~15ms local network RTT).
* **🎮 Dual Input Injection Bridge**:
  * **Virtual Xbox 360 Controller (`vgamepad`)**: Native XInput controller support recognized by Steam, PC games, and emulators.
  * **Windows Keyboard Injection (`pynput`)**: Fallback WASD + Arrow Keys + Spacebar mapping for standard PC executable games.
* **🔒 Game Lock Mode & Focus Blurring**: Prevents Switch D-Pad/Button presses from highlighting or interacting with HTML webpage elements.
* **👁️ Minimal HUD View**: Toggle between detailed real-time telemetry metrics and a clean full-screen view with only a floating FPS badge (`60 FPS`).
* **🕹️ Included Sample 60 FPS Game**: Comes with `game.py` (2D Space Defender PC arcade game) for immediate out-of-the-box demonstration.

---

## 🏗️ Architecture Pipeline

```text
  +-------------------------------------------------------------------+
  |                           GAMING PC                               |
  |                                                                   |
  |  +--------------------+         +------------------------------+  |
  |  |  PC Game / Desktop |         |  Virtual Xbox 360 Controller |  |
  |  +---------+----------+         +--------------^---------------+  |
  |            | (DXCAM GPU)                       | (vgamepad /    |
  |            v                                   |  pynput)       |
  |  +---------------------------------------------+---------------+  |
  |  |                 Starlette / Uvicorn Server                  |  |
  |  +---------------------+-----------------------^----------------+  |
  +------------------------|-----------------------|------------------+
                           | Binary JPEG           | Telemetry JSON
                           | (WebSocket)           | (Gamepad API)
                           v                       |
  +------------------------------------------------|------------------+
  |                   NINTENDO SWITCH LITE (STOCK)                 |
  |                                                                   |
  |  +-------------------------------------------------------------+  |
  |  |       Hidden WebKit Browser (HTML5 Canvas / Image)          |  |
  |  |   - Render Engine: Image / createImageBitmap (720p @ 60FPS)  |  |
  |  |   - Gamepad API: Polls Sticks & Buttons @ 60 Hz             |  |
  |  +-------------------------------------------------------------+  |
  +-------------------------------------------------------------------+
```

---

## 📊 Benchmark Results

Benchmarked on **1280x720 (Native Switch Lite Resolution)** over local Wi-Fi:

| Resolution | Quality | Server Encode Latency | Server FPS Ceiling | Bandwidth @ 60FPS |
|:----------:|:-------:|:---------------------:|:------------------:|:-----------------:|
| **360p** | 50% | 0.45 ms | 2,211 FPS | 5.08 Mbps |
| **480p** | 50% | 0.86 ms | 1,163 FPS | 7.37 Mbps |
| **720p** | **50% (Recommended)** | **1.62 ms** | **618 FPS** | **12.87 Mbps** |
| **720p** | 75% | 1.63 ms | 613 FPS | 14.79 Mbps |

---

## 🛠️ Step-by-Step Setup Guide

### 1. Requirements on Gaming PC
* **Windows 10 / 11**
* **Python 3.10+**

Install required dependencies:
```bash
pip install starlette uvicorn opencv-python pillow numpy websockets dxcam vgamepad pynput pygame
```

### 2. Start the PC Server & Controller Bridge
In PowerShell or Command Prompt:
```bash
python server.py
```
*The terminal will output your PC's local network IP address (e.g. `http://192.168.1.6:8080`).*

### 3. Launch the Included Sample Game (Optional)
In a second terminal:
```bash
python game.py
```
*(Or open any Steam game, Xbox Game Pass title, or emulator on your PC desktop!)*

### 4. Connect Your Stock Nintendo Switch Lite
1. Go to **System Settings** → **Internet** → **Internet Settings** on your Switch Lite.
2. Select your Wi-Fi network → **Change Settings**.
3. Set **DNS Settings** to **Manual**.
4. Set **Primary DNS** to `45.55.142.122` (SwitchBru DNS).
5. Save and select **Connect to This Network**.
6. When prompted, tap **Next** to open the captive portal web browser.
7. Enter your PC's URL (e.g., `http://192.168.1.6:8080`).
8. Select **DESKTOP** (Source), **Image** (Engine), and **720p 60FPS**.
9. Click **`👁️ MINIMAL HUD`** for full-screen game streaming!

---

## 🕹️ Input Mapping Matrix

| Switch Lite Button | Virtual Xbox 360 Button | Windows Keyboard Fallback |
|:------------------:|:-----------------------:|:-------------------------:|
| **Left Stick** | Left Joystick | `W` / `A` / `S` / `D` |
| **D-Pad** | D-Pad Up / Down / Left / Right | Arrow Keys |
| **Switch B** | Xbox `A` | `Spacebar` / `Z` |
| **Switch A** | Xbox `B` | `Z` / `J` |
| **Switch Y** | Xbox `X` | `X` |
| **Switch X** | Xbox `Y` | `C` |
| **Switch L / R** | Shoulder LB / RB | `Shift` |
| **Switch ZL / ZR** | Triggers LT / RT | `Spacebar` |
| **Switch - (Minus)** | Back / Select | `Escape` |
| **Switch + (Plus)** | Start | `Enter` |

---

## 📜 Disclaimer & Legal Notice

This project is an independent open-source research demonstration of low-latency local network streaming using standard web technologies.

* **Nintendo Switch** and **Nintendo Switch Lite** are registered trademarks of Nintendo Co., Ltd.
* This project is not affiliated with, endorsed by, or sponsored by Nintendo Co., Ltd.
* All code in this repository is 100% original and uses public APIs.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
