import os, sys, math, cv2, numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Virtual Volume Control"
DESCRIPTION = "Adjust master audio and send PWM output based on pinch distance."
ICON = "🔊"
device_state = {'status': 'Active', 'volume_level': '50%'}

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_ctl = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume_ctl.GetVolumeRange()
    min_vol, max_vol = vol_range[0], vol_range[1]
except Exception:
    volume_ctl = None
    min_vol, max_vol = -65.0, 0.0

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    if not cap.isOpened(): cap = cv2.VideoCapture(0)

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            if res.multi_hand_landmarks:
                for hlms in res.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hlms, mp_hands.HAND_CONNECTIONS)
                    lms = hlms.landmark
                    x1, y1 = int(lms[4].x * w), int(lms[4].y * h)
                    x2, y2 = int(lms[8].x * w), int(lms[8].y * h)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    cv2.circle(frame, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                    cv2.circle(frame, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    dist = math.hypot(x2 - x1, y2 - y1)
                    vol_pct = int(np.interp(dist, [25, 180], [0, 100]))
                    target_vol = np.interp(dist, [25, 180], [min_vol, max_vol])

                    if volume_ctl:
                        try: volume_ctl.SetMasterVolumeLevel(target_vol, None)
                        except Exception: pass

                    device_state['volume_level'] = f'{vol_pct}%'
                    iot.send(f'VOL_PWM_{vol_pct}')

                    bar_y = int(np.interp(vol_pct, [0, 100], [380, 140]))
                    cv2.rectangle(frame, (40, 140), (70, 380), (0, 255, 0), 2)
                    cv2.rectangle(frame, (40, bar_y), (70, 380), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, f'{vol_pct}%', (35, 415), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
