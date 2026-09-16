import asyncio
import io
import json
import math
import os
import time
import socket
import struct
import numpy as np
import cv2
from PIL import ImageGrab

from starlette.applications import Starlette
from starlette.responses import Response, StreamingResponse, HTMLResponse, FileResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
import uvicorn

# Global Configuration State
class StreamState:
    def __init__(self):
        self.resolution = "720p"  # "360p", "480p", "720p"
        self.fps = 30
        self.quality = 50
        self.mode = "synthetic"  # "synthetic" or "desktop"
        self.render_method = "createImageBitmap"
        
        self.width = 1280
        self.height = 720
        self.frame_id = 0
        self.start_time = time.time()
        
        # Bouncing ball state for synthetic mode
        self.ball_x = 200.0
        self.ball_y = 200.0
        self.ball_vx = 320.0  # px/sec
        self.ball_vy = 220.0  # px/sec
        self.ball_radius = 40
        
        # Telemetry & Gamepad metrics
        self.sent_frames = 0
        self.bytes_sent = 0
        self.last_stat_reset = time.time()
        self.latest_gamepad = {
            "connected": False,
            "axes": [0.0, 0.0, 0.0, 0.0],
            "buttons": [],
            "timestamp": 0
        }

    def update_resolution(self, res_str):
        self.resolution = res_str
        if res_str == "360p":
            self.width, self.height = 640, 360
        elif res_str == "480p":
            self.width, self.height = 854, 480
        elif res_str == "720p":
            self.width, self.height = 1280, 720
        else:
            self.width, self.height = 1280, 720
        self.ball_radius = max(20, int(min(self.width, self.height) * 0.06))

state = StreamState()

try:
    import vgamepad as vg
    virtual_gamepad = vg.VX360Gamepad()
    print("[VIRTUAL CONTROLLER] Xbox 360 Controller initialized successfully!")
except Exception as e:
    virtual_gamepad = None
    print(f"[VIRTUAL CONTROLLER WARNING] Could not initialize vgamepad: {e}")

try:
    from pynput.keyboard import Key, Controller as KeyboardController
    keyboard_controller = KeyboardController()
    print("[KEYBOARD BRIDGE] Windows Keyboard Injection initialized successfully!")
except Exception as e:
    keyboard_controller = None
    print(f"[KEYBOARD BRIDGE WARNING] Could not initialize pynput keyboard: {e}")

try:
    from pynput.mouse import Controller as MouseController, Button as MouseButton
    mouse_controller = MouseController()
    print("[MOUSE BRIDGE] Windows Mouse Injection initialized successfully!")
except Exception as e:
    mouse_controller = None
    print(f"[MOUSE BRIDGE WARNING] Could not initialize pynput mouse: {e}")

active_pressed_keys = set()
active_pressed_mouse_buttons = set()

KEYMAP_FILE = os.path.join(os.path.dirname(__file__), "keymap.json")

def load_keymap():
    """Load customizable keymap configuration from keymap.json."""
    if os.path.exists(KEYMAP_FILE):
        try:
            with open(KEYMAP_FILE, "r") as f:
                data = json.load(f)
                print(f"[KEYMAP ENGINE] Loaded custom keymap from keymap.json")
                return data
        except Exception as e:
            print(f"[KEYMAP WARNING] Could not parse keymap.json: {e}")
    return {}

keymap_config = load_keymap()

XBOX_BTN_MAP = {}
if virtual_gamepad and hasattr(vg, 'XUSB_BUTTON'):
    XBOX_BTN_MAP = {
        "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "LEFT_SHOULDER": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "RIGHT_SHOULDER": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "LEFT_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        "RIGHT_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT
    }

def resolve_pynput_key(key_str):
    k = str(key_str).lower()
    special = {
        "left": Key.left, "right": Key.right, "up": Key.up, "down": Key.down,
        "space": Key.space, "esc": Key.esc, "enter": Key.enter,
        "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt, "tab": Key.tab,
        "caps_lock": Key.caps_lock, "backspace": Key.backspace
    }
    return special.get(k, k)

def update_virtual_controller(gp_data):
    """Translate Switch Lite Gamepad API data to Virtual Xbox 360 Controller AND Windows Keyboard/Mouse Events via keymap.json."""
    axes = gp_data.get("axes", [0, 0, 0, 0])
    buttons = gp_data.get("buttons", [])
    
    # Reload keymap if modified
    global keymap_config
    if not keymap_config:
        keymap_config = load_keymap()
        
    xb_config = keymap_config.get("xbox_mapping", {})
    kb_config = keymap_config.get("keyboard_mapping", {})
    
    # --- 1. XBOX 360 CONTROLLER INJECTION (vgamepad) ---
    if virtual_gamepad:
        try:
            # Left Joystick (WASD / Movement)
            lx = float(axes[0]) if len(axes) > 0 else 0.0
            ly = float(axes[1]) if len(axes) > 1 else 0.0
            if abs(lx) < 0.03: lx = 0.0
            if abs(ly) < 0.03: ly = 0.0
            virtual_gamepad.left_joystick(x_value=int(lx * 32767), y_value=int(-ly * 32767))
            
            # Right Joystick (Camera / Aiming) with Multi-Axis Scanning
            rx = 0.0
            ry = 0.0
            if len(axes) > 3:
                rx = float(axes[2])
                ry = float(axes[3])
                # WebKit fallback scanning if right stick is mapped to higher axis indices
                if abs(rx) < 0.03 and len(axes) > 4 and abs(float(axes[4])) > 0.03:
                    rx = float(axes[4])
                if abs(ry) < 0.03 and len(axes) > 5 and abs(float(axes[5])) > 0.03:
                    ry = float(axes[5])
                    
            if abs(rx) < 0.03: rx = 0.0
            if abs(ry) < 0.03: ry = 0.0
            
            if abs(rx) > 0.05 or abs(ry) > 0.05:
                print(f"[RIGHT STICK DEBUG] rx={rx:.3f}, ry={ry:.3f} | Raw Axes: {[round(a, 2) for a in axes]}")

            virtual_gamepad.right_joystick(x_value=int(rx * 32767), y_value=int(-ry * 32767))
            
            # Dynamic Xbox Button Mapping from keymap.json
            for sw_str, xb_name in xb_config.items():
                try:
                    sw_idx = int(sw_str)
                    xbox_btn = XBOX_BTN_MAP.get(xb_name)
                    if xbox_btn:
                        if sw_idx < len(buttons) and buttons[sw_idx]:
                            virtual_gamepad.press_button(button=xbox_btn)
                        else:
                            virtual_gamepad.release_button(button=xbox_btn)
                except Exception:
                    pass
                    
            zl_pressed = (len(buttons) > 6 and buttons[6]) or (len(axes) > 4 and axes[4] > 0.5)
            zr_pressed = (len(buttons) > 7 and buttons[7]) or (len(axes) > 5 and axes[5] > 0.5)
            
            virtual_gamepad.left_trigger_float(value_float=1.0 if zl_pressed else 0.0)
            virtual_gamepad.right_trigger_float(value_float=1.0 if zr_pressed else 0.0)
            
            virtual_gamepad.update()
        except Exception as ex:
            pass

    # --- 2. WINDOWS KEYBOARD & MOUSE INJECTION (pynput) ---
    if keyboard_controller or mouse_controller:
        try:
            target_keys = set()
            target_mouse = set()
            
            lx = float(axes[0]) if len(axes) > 0 else 0.0
            ly = float(axes[1]) if len(axes) > 1 else 0.0
            
            # Left Stick Keyboard Mapping (WASD)
            if lx < -0.2:
                for k in kb_config.get("left_stick_left", []): target_keys.add(resolve_pynput_key(k))
            if lx > 0.2:
                for k in kb_config.get("left_stick_right", []): target_keys.add(resolve_pynput_key(k))
            if ly < -0.2:
                for k in kb_config.get("left_stick_up", []): target_keys.add(resolve_pynput_key(k))
            if ly > 0.2:
                for k in kb_config.get("left_stick_down", []): target_keys.add(resolve_pynput_key(k))

            # Right Stick Camera Movement (Mouse & Arrow Key Fallbacks)
            rx = 0.0
            ry = 0.0
            if len(axes) > 3:
                rx = float(axes[2])
                ry = float(axes[3])
                if abs(rx) < 0.03 and len(axes) > 4 and abs(float(axes[4])) > 0.03:
                    rx = float(axes[4])
                if abs(ry) < 0.03 and len(axes) > 5 and abs(float(axes[5])) > 0.03:
                    ry = float(axes[5])

            if rx < -0.2:
                for k in kb_config.get("right_stick_left", []): target_keys.add(resolve_pynput_key(k))
            if rx > 0.2:
                for k in kb_config.get("right_stick_right", []): target_keys.add(resolve_pynput_key(k))
            if ry < -0.2:
                for k in kb_config.get("right_stick_up", []): target_keys.add(resolve_pynput_key(k))
            if ry > 0.2:
                for k in kb_config.get("right_stick_down", []): target_keys.add(resolve_pynput_key(k))

            if mouse_controller and (abs(rx) > 0.03 or abs(ry) > 0.03):
                dx = int(rx * 40)
                dy = int(ry * 40)
                mouse_controller.move(dx, dy)
                
            # Direct Button Keyboard & Mouse Mapping
            for sw_idx in range(len(buttons)):
                if buttons[sw_idx]:
                    btn_keys = kb_config.get(f"button_{sw_idx}", [])
                    for k in btn_keys:
                        k_str = str(k).lower()
                        if k_str in ["right_click", "right_mouse", "mouse_right"]:
                            target_mouse.add("right")
                        elif k_str in ["left_click", "left_mouse", "mouse_left"]:
                            target_mouse.add("left")
                        else:
                            target_keys.add(resolve_pynput_key(k))
                            
            # Explicit ZL & ZR triggers if mapped or axis pressed
            zl_pressed = (len(buttons) > 6 and buttons[6]) or (len(axes) > 4 and axes[4] > 0.5)
            zr_pressed = (len(buttons) > 7 and buttons[7]) or (len(axes) > 5 and axes[5] > 0.5)
            if zl_pressed: target_mouse.add("right")
            if zr_pressed: target_mouse.add("left")
                        
            # Apply Keyboard key presses and releases
            if keyboard_controller:
                keys_to_press = target_keys - active_pressed_keys
                keys_to_release = active_pressed_keys - target_keys
                
                for k in keys_to_release:
                    try: keyboard_controller.release(k)
                    except Exception: pass
                    
                for k in keys_to_press:
                    try: keyboard_controller.press(k)
                    except Exception: pass
                    
                active_pressed_keys.clear()
                active_pressed_keys.update(target_keys)
                
            # Apply Mouse button clicks and releases
            if mouse_controller:
                m_to_press = target_mouse - active_pressed_mouse_buttons
                m_to_release = active_pressed_mouse_buttons - target_mouse
                
                for m in m_to_release:
                    try:
                        if m == "right": mouse_controller.release(MouseButton.right)
                        elif m == "left": mouse_controller.release(MouseButton.left)
                    except Exception: pass
                    
                for m in m_to_press:
                    try:
                        if m == "right": mouse_controller.press(MouseButton.right)
                        elif m == "left": mouse_controller.press(MouseButton.left)
                    except Exception: pass
                    
                active_pressed_mouse_buttons.clear()
                active_pressed_mouse_buttons.update(target_mouse)
        except Exception as ex:
            pass

def get_local_ip():
    """Find local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_synthetic_frame(dt):
    """Generate a high-motion synthetic benchmark frame with timestamps and bouncing logo."""
    state.frame_id += 1
    w, h = state.width, state.height
    
    # Update bouncing ball physics
    state.ball_x += state.ball_vx * dt
    state.ball_y += state.ball_vy * dt
    
    r = state.ball_radius
    if state.ball_x - r < 0:
        state.ball_x = r
        state.ball_vx *= -1
    elif state.ball_x + r > w:
        state.ball_x = w - r
        state.ball_vx *= -1
        
    if state.ball_y - r < 0:
        state.ball_y = r
        state.ball_vy *= -1
    elif state.ball_y + r > h:
        state.ball_y = h - r
        state.ball_vy *= -1
        
    # Canvas background - dynamic hue shift
    curr_time = time.time()
    rel_time = curr_time - state.start_time
    hue = int((rel_time * 40) % 180)
    hsv_bg = np.full((h, w, 3), (hue, 120, 45), dtype=np.uint8)
    frame = cv2.cvtColor(hsv_bg, cv2.COLOR_HSV2BGR)
    
    # Grid overlay
    grid_size = 40 if w >= 854 else 20
    for x in range(0, w, grid_size):
        cv2.line(frame, (x, 0), (x, h), (60, 60, 60), 1)
    for y in range(0, h, grid_size):
        cv2.line(frame, (0, y), (w, y), (60, 60, 60), 1)
        
    # Draw animated color spectrum wheel/bar at bottom
    bar_h = 24 if h >= 720 else 14
    spectrum = np.linspace(0, 179, w, dtype=np.int32)
    shift = int((rel_time * 60) % 180)
    spectrum_img = np.zeros((bar_h, w, 3), dtype=np.uint8)
    spectrum_img[:, :, 0] = ((spectrum + shift) % 180).astype(np.uint8)
    spectrum_img[:, :, 1] = 255
    spectrum_img[:, :, 2] = 255
    spectrum_bgr = cv2.cvtColor(spectrum_img, cv2.COLOR_HSV2BGR)
    frame[h - bar_h:h, 0:w] = spectrum_bgr

    # Draw Bouncing Ball with glow & gradient
    bx, by = int(state.ball_x), int(state.ball_y)
    ball_color = (0, 255, 255) # Yellow/Cyan
    cv2.circle(frame, (bx, by), r, ball_color, -1)
    cv2.circle(frame, (bx, by), r, (255, 255, 255), 3)
    cv2.putText(frame, "TEST 3", (bx - int(r*0.7), by + 5), cv2.FONT_HERSHEY_SIMPLEX, 
                0.5 if w < 854 else 0.8, (0, 0, 0), 2)
    
    # Draw Header Information Block
    now_ms = int((time.time() - state.start_time) * 1000)
    time_str = time.strftime("%H:%M:%S", time.localtime()) + f".{int((time.time() % 1) * 1000):03d}"
    
    font_scale = 0.5 if w < 854 else 0.8
    thickness = 2
    
    # Top overlay header box
    cv2.rectangle(frame, (10, 10), (w - 10, 95 if h >= 720 else 65), (20, 20, 20), -1)
    cv2.rectangle(frame, (10, 10), (w - 10, 95 if h >= 720 else 65), (0, 220, 255), 2)
    
    line1 = f"SWITCH LITE STREAM TEST 3 - {state.resolution} @ {state.fps}FPS (Q:{state.quality}%)"
    line2 = f"FRAME: #{state.frame_id} | TIME: {time_str} | MODE: {state.mode.upper()}"
    
    cv2.putText(frame, line1, (20, 35 if h >= 720 else 30), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
    cv2.putText(frame, line2, (20, 70 if h >= 720 else 55), cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.9, (255, 255, 255), 1)

    # Gamepad status overlay on frame
    gp = state.latest_gamepad
    if gp and gp.get("connected"):
        axes = gp.get("axes", [0, 0, 0, 0])
        lx, ly = axes[0] if len(axes) > 0 else 0, axes[1] if len(axes) > 1 else 0
        rx, ry = axes[2] if len(axes) > 2 else 0, axes[3] if len(axes) > 3 else 0
        
        # Stick visualizers
        center_lx = w - 140
        center_ly = h - 100
        cv2.circle(frame, (center_lx, center_ly), 30, (80, 80, 80), 2)
        cv2.circle(frame, (int(center_lx + lx * 25), int(center_ly + ly * 25)), 8, (0, 255, 0), -1)
        
        center_rx = w - 60
        center_ry = h - 100
        cv2.circle(frame, (center_rx, center_ry), 30, (80, 80, 80), 2)
        cv2.circle(frame, (int(center_rx + rx * 25), int(center_ry + ry * 25)), 8, (255, 0, 255), -1)
        
        cv2.putText(frame, "SWITCH GAMEPAD", (w - 180, h - 145), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Encode frame to JPEG
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), state.quality]
    _, jpeg_buf = cv2.imencode('.jpg', frame, encode_param)
    return jpeg_buf.tobytes()

# DXCAM ultra-fast GPU screen capture initialization
try:
    import dxcam
    dx_camera = dxcam.create(output_color="BGR")
    dx_camera.start(target_fps=60, video_mode=True)
    print("[CAPTURE ENGINE] DXCAM DirectX Desktop Duplication GPU capture enabled (1000+ FPS capability)!")
except Exception as e:
    dx_camera = None
    print(f"[CAPTURE ENGINE WARNING] DXCAM fallback to PIL/OpenCV: {e}")

def capture_desktop_frame():
    """Capture live Windows desktop and convert to JPEG."""
    state.frame_id += 1
    w, h = state.width, state.height
    try:
        frame = None
        global dx_camera
        if dx_camera:
            try:
                frame = dx_camera.get_latest_frame()
            except Exception:
                pass
                
        if frame is None:
            img = ImageGrab.grab()
            img_np = np.array(img)
            # Convert RGB to BGR
            frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
        frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Overlay frame counter & timestamp
        time_str = time.strftime("%H:%M:%S", time.localtime()) + f".{int((time.time() % 1) * 1000):03d}"
        overlay_txt = f"LIVE DESKTOP #{state.frame_id} | {time_str} | {state.resolution}@{state.fps}FPS Q:{state.quality}%"
        cv2.putText(frame_resized, overlay_txt, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), state.quality]
        _, jpeg_buf = cv2.imencode('.jpg', frame_resized, encode_param)
        return jpeg_buf.tobytes()
    except Exception as e:
        print(f"Desktop capture error: {e}")
        return generate_synthetic_frame(0.033)

def get_next_frame(dt):
    """Fetch next frame according to current mode."""
    if state.mode == "desktop":
        return capture_desktop_frame()
    else:
        return generate_synthetic_frame(dt)

# Starlette Routes & Endpoints
async def homepage(request):
    """Serve main HTML app."""
    return FileResponse("index.html")

async def get_mjpeg_stream(request):
    """HTTP MJPEG endpoint for Test 4 streaming evaluation."""
    async def mjpeg_generator():
        last_time = time.time()
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now
            
            target_dt = 1.0 / max(1, state.fps)
            frame_bytes = get_next_frame(dt)
            
            header = (
                f"--frame\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame_bytes)}\r\n\r\n"
            ).encode("utf-8")
            yield header + frame_bytes + b"\r\n"
            
            elapsed = time.time() - now
            sleep_time = max(0.001, target_dt - elapsed)
            await asyncio.sleep(sleep_time)

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint streaming binary JPEG frames + JSON telemetry."""
    await websocket.accept()
    print("Client connected via WebSocket!")
    
    last_time = time.time()
    
    async def receive_messages():
        """Listen for control commands and gamepad input from client."""
        try:
            while True:
                msg_text = await websocket.receive_text()
                try:
                    data = json.loads(msg_text)
                    msg_type = data.get("type")
                    
                    if msg_type == "config":
                        if "resolution" in data:
                            state.update_resolution(data["resolution"])
                        if "fps" in data:
                            state.fps = int(data["fps"])
                        if "quality" in data:
                            state.quality = int(data["quality"])
                        if "mode" in data:
                            state.mode = str(data["mode"])
                        if "renderMethod" in data:
                            state.render_method = str(data["renderMethod"])
                        print(f"Updated config: {state.resolution} @ {state.fps}FPS, Q:{state.quality}%, Mode:{state.mode}")
                        
                        # Send ack
                        await websocket.send_text(json.dumps({
                            "type": "config_ack",
                            "resolution": state.resolution,
                            "fps": state.fps,
                            "quality": state.quality,
                            "mode": state.mode,
                            "renderMethod": state.render_method
                        }))

                    elif msg_type == "ping":
                        client_ts = data.get("timestamp", 0)
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "clientTimestamp": client_ts,
                            "serverTimestamp": int(time.time() * 1000)
                        }))

                    elif msg_type == "gamepad":
                        state.latest_gamepad = data
                        update_virtual_controller(data)
                        
                except Exception as ex:
                    print(f"Error parsing websocket message: {ex}")
        except WebSocketDisconnect:
            print("WebSocket client disconnected from receive loop.")
        except Exception as e:
            print(f"WebSocket receive exception: {e}")

    # Task to handle incoming messages
    rx_task = asyncio.create_task(receive_messages())
    
    try:
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now
            
            target_dt = 1.0 / max(1, state.fps)
            frame_bytes = get_next_frame(dt)
            
            # Pack binary frame header:
            # Struct format: !III (3x 32-bit unsigned uints: frame_id, timestamp_ms, jpeg_len)
            ts_ms = int((now - state.start_time) * 1000) & 0xFFFFFFFF
            header = struct.pack("!III", state.frame_id, ts_ms, len(frame_bytes))
            payload = header + frame_bytes
            
            await websocket.send_bytes(payload)
            state.sent_frames += 1
            state.bytes_sent += len(payload)
            
            elapsed = time.time() - now
            sleep_time = max(0.001, target_dt - elapsed)
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"WebSocket send loop ended: {e}")
    finally:
        rx_task.cancel()

routes = [
    Route('/', homepage),
    Route('/mjpeg', get_mjpeg_stream),
    WebSocketRoute('/ws', websocket_endpoint),
    Mount('/static', app=StaticFiles(directory='.'), name='static')
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8080
    print("=" * 70)
    print("  STOCK NINTENDO SWITCH LITE PC STREAMING SERVER - TEST 3")
    print("=" * 70)
    print(f" Local Computer Address : http://localhost:{port}")
    print(f" Nintendo Switch Lite URL: http://{local_ip}:{port}")
    print(f" MJPEG Endpoint Stream  : http://{local_ip}:{port}/mjpeg")
    print("=" * 70)
    print(" Connect your Switch Lite using SwitchBru DNS (45.55.142.122)")
    print(" Enter the URL above in the browser to start benchmarking!")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
