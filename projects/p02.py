import os
import sys
import cv2
import math
import numpy as np

# Ensure root directory is on the path for iot_bridge
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from iot_bridge import iot

# Robust MediaPipe solutions import
import mediapipe as mp
try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Virtual Volume Control"
DESCRIPTION = "Adjust system master volume and output IoT PWM levels by pinching fingers."
ICON = "🔊"

device_state = {"volume_level": 50, "status": "Ready"}

# Safe PyCaw audio endpoint initialization
has_pycaw = False
volume_control = None
min_vol, max_vol = -65.25, 0.0

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_control = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume_control.GetVolumeRange()
    min_vol, max_vol = vol_range[0], vol_range[1]
    has_pycaw = True
except Exception:
    has_pycaw = False

def generate_frames():
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_lms in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
                    lms = hand_lms.landmark
                    
                    # Coordinates of Thumb tip (4) and Index tip (8)
                    x1, y1 = int(lms[4].x * w), int(lms[4].y * h)
                    x2, y2 = int(lms[8].x * w), int(lms[8].y * h)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    cv2.circle(frame, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                    cv2.circle(frame, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    cv2.circle(frame, (cx, cy), 6, (0, 255, 0), cv2.FILLED)

                    dist = math.hypot(x2 - x1, y2 - y1)
                    
                    # Interpolate distance to percentage (0 - 100) and audio dB range
                    vol_percent = int(np.interp(dist, [25, 180], [0, 100]))
                    target_vol = np.interp(dist, [25, 180], [min_vol, max_vol])

                    if has_pycaw and volume_control:
                        try:
                            volume_control.SetMasterVolumeLevel(target_vol, None)
                        except Exception:
                            pass

                    device_state["volume_level"] = vol_percent
                    device_state["status"] = "Tracking"
                    iot.send(f"VOL_PWM_{vol_percent}")

                    # Visual feedback bar
                    cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 2)
                    bar_h = int(np.interp(vol_percent, [0, 100], [400, 150]))
                    cv2.rectangle(frame, (50, bar_h), (85, 400), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, f"{vol_percent}%", (45, 430),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    cap.release()