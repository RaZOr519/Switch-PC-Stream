# 🎮 SwitchLite-PC-Stream

> **Low-Latency PC Game Streaming Engine for Stock, Unmodded Nintendo Switch Lite**  
> *Stream 720p @ 60 FPS over local network using the Switch's native WebKit browser!*

![Release](https://img.shields.io/badge/Release-v0.0.1-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Resolution](https://img.shields.io/badge/Resolution-1280x720%20%40%2060FPS-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Nintendo%20Switch%20Lite%20%28Stock%2FUnmodded%29-red.svg)
[![Ko-fi](https://img.shields.io/badge/Support%20Me-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/sachindewthuru)

---

## 🎥 Demonstration Media

Check out live video test runs of the Nintendo Switch Lite streaming PC games at 720p @ 60 FPS over local network:

* 🎬 **[Watch Demo Video 1 (Gameplay Stream Test)](https://github.com/RaZOr519/Switch-PC-Stream/blob/main/media/demo1.mp4)**
* 🎬 **[Watch Demo Video 2 (Input Latency & Controls Test)](https://github.com/RaZOr519/Switch-PC-Stream/blob/main/media/demo2.mp4)**

---

## ⚡ Overview

**SwitchLite-PC-Stream** is a high-performance, low-latency open-source game streaming system designed to play any PC game, emulator, or desktop title on a **completely stock Nintendo Switch Lite** without modchips, jailbreaks, Android/Linux installations, or custom firmware.

By utilizing the Switch's hidden captive-portal WebKit browser (accessible via SwitchBru DNS), the system establishes a low-overhead WebSocket stream using DirectX 11 GPU Desktop Duplication (`dxcam`) and optimized JPEG frame compression. Physical controls (Analog Sticks, D-Pad, Buttons, Triggers) are captured via the WebKit HTML5 Gamepad API and transmitted back to the host PC in real-time, injecting them as **Virtual Xbox 360 Controller (XInput)** and **Hardware Raw Mouse/Keyboard** events.

---

## 🌟 Key Features

* **⚡ Ultra-Fast GPU Capture**: DirectX 11 GPU Desktop Duplication API (`dxcam`) provides **0.53 ms capture latency (1,899 FPS capability)**.
* **🎯 720p @ 60 FPS Local Network Streaming**: Native 1280x720 resolution scaled for the Switch Lite screen with ultra-low end-to-end latency (~15 ms RTT).
* **🎮 Universal Dual Input Engine**:
  * **Virtual Xbox 360 Controller (`vgamepad`)**: Full 16-bit XInput controller emulation recognized by Steam, AAA PC titles, and emulators.
  * **Hardware Raw Mouse & Keyboard Injection (`ctypes` + `pynput`)**: Direct Win32 `mouse_event` delta movement for 3D camera look (FPS/TPS) and WASD key injection.
* **🕹️ Modular Keymap System (`keymap.json`)**: Reassign Xbox XInput and Keyboard/Mouse bindings for any game via simple JSON configuration.
* **🔒 WebKit Navigation Trap**: `history.pushState` and `popstate` intercept physical Switch button presses (like B) to prevent unwanted browser navigation.
* **👁️ Minimal HUD Mode**: Toggle between real-time network telemetry metrics and a clean full-screen view with a floating FPS counter (`60 FPS`).
* **🕹️ Out-of-the-Box Demo Game**: Includes `game.py` (a 2D PC arcade game) for immediate verification after setup.

---

## 🏗️ System Architecture

```text
  +-------------------------------------------------------------------+
  |                           HOST GAMING PC                          |
  |                                                                   |
  |  +--------------------+         +------------------------------+  |
  |  |   PC Game / App    |         |  Virtual Xbox 360 Controller |  |
  |  +---------+----------+         +--------------^---------------+  |
  |            | (DXCAM GPU Capture)               | (vgamepad /    |
  |            v                                   |  raw mouse)    |
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

## 📊 Benchmark Telemetry

Tested on a local 5GHz Wi-Fi network at native **1280x720 (Switch Lite resolution)**:

| Resolution | Quality | Host Encode Latency | Frame Capture Rate | Bandwidth @ 60FPS |
|:----------:|:-------:|:------------------:|:------------------:|:-----------------:|
| **360p** | 50% | 0.45 ms | 2,211 FPS | 5.08 Mbps |
| **480p** | 50% | 0.86 ms | 1,163 FPS | 7.37 Mbps |
| **720p** | **50% (Recommended)** | **1.62 ms** | **618 FPS** | **12.87 Mbps** |
| **720p** | 75% | 1.63 ms | 613 FPS | 14.79 Mbps |

---

## 🛠️ Installation & Setup

### 1. Host PC Requirements
* **Windows 10 / 11 (64-bit)**
* **Python 3.10+**
* **ViGEmBus Driver (Required for Virtual Xbox 360 Controller)**:
  * Install the ViGEmBus driver on your PC from the official release page: [Download ViGEmBus_Setup.exe](https://github.com/nefarius/ViGEmBus/releases/latest).

Install Python dependencies:
```bash
pip install starlette uvicorn opencv-python pillow numpy websockets dxcam vgamepad pynput pygame
```

### 2. Launch Server
Run the streaming server in PowerShell or Command Prompt:
```bash
python server.py
```
*The server will display your PC's local IP address (e.g. `http://192.168.1.6:8080`).*

### 3. Connect Nintendo Switch Lite
1. Go to **System Settings** → **Internet** → **Internet Settings** on your Switch Lite.
2. Select your Wi-Fi network → **Change Settings**.
3. Set **DNS Settings** to **Manual**.
4. Set **Primary DNS** to `45.55.142.122` (SwitchBru DNS).
5. Save and select **Connect to This Network**.
6. When prompted, tap **Next** to open the captive portal web browser.
7. Enter your PC's URL (e.g. `http://192.168.1.6:8080`).
8. Select **DESKTOP** (Source), **Image** (Engine), and **720p 60FPS**.
9. Click **`🔒 LOCK UI`** and **`👁️ MINIMAL HUD`** to begin streaming!

---

## 🕹️ Input Configuration (`keymap.json`)

All controller buttons and axis behaviors are customizable in **`keymap.json`**:

```json
{
  "xbox_mapping": {
    "0": "A",
    "1": "B",
    "2": "X",
    "3": "Y",
    "4": "LEFT_SHOULDER",
    "5": "RIGHT_SHOULDER",
    "8": "BACK",
    "9": "START",
    "12": "DPAD_UP",
    "13": "DPAD_DOWN",
    "14": "DPAD_LEFT",
    "15": "DPAD_RIGHT"
  },
  "keyboard_mapping": {
    "left_stick_left": ["a"],
    "left_stick_right": ["d"],
    "left_stick_up": ["w"],
    "left_stick_down": ["s"],
    "button_0": ["shift"],
    "button_1": ["r"],
    "button_2": ["space"],
    "button_3": ["f"],
    "button_4": ["tab"],
    "button_5": ["q"]
  }
}
```

---

## 📜 Disclaimer & Legal Notice

This repository is an open-source technical demonstration of low-latency local streaming using standard web protocols.

* **Nintendo Switch** and **Nintendo Switch Lite** are registered trademarks of Nintendo Co., Ltd.
* This project is independent and is not affiliated with, endorsed by, or sponsored by Nintendo Co., Ltd.
* All code in this repository is original and relies exclusively on public web and operating system APIs.

---

## ❤️ Contributing & Donations

Contributions and pull requests are welcome! If you find this project useful, feel free to support development on Ko-fi:

<a href="https://ko-fi.com/sachindewthuru" target="_blank"><img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support Me on Ko-fi"></a>

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
