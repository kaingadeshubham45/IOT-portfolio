import os, sys, math, time, cv2, numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Virtual Mouse Control"
DESCRIPTION = "Cursor navigation via single index finger and dwell hover-click."
ICON = "🖱️"
device_state = {'status': 'Active', 'action': 'Searching Hand'}

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    sw, sh = pyautogui.size()
    has_pyautogui = True
except Exception:
    has_pyautogui = False
    sw, sh = 1920, 1080

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    if not cap.isOpened(): cap = cv2.VideoCapture(0)
    
    hover_time = None
    last_x, last_y = 0, 0
    smoothening = 4
    cloc_x, cloc_y = 0, 0

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6) as hands:
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
                    idx_up = lms[8].y < lms[6].y
                    mid_up = lms[12].y < lms[10].y

                    if idx_up and not mid_up:
                        ix, iy = int(lms[8].x * w), int(lms[8].y * h)
                        target_x = np.interp(ix, [50, w - 50], [0, sw])
                        target_y = np.interp(iy, [50, h - 50], [0, sh])
                        cloc_x += (target_x - cloc_x) / smoothening
                        cloc_y += (target_y - cloc_y) / smoothening

                        if has_pyautogui:
                            try: pyautogui.moveTo(int(cloc_x), int(cloc_y), _pause=False)
                            except Exception: pass

                        if math.hypot(ix - last_x, iy - last_y) < 20:
                            if hover_time is None: hover_time = time.time()
                            prog = min(1.0, (time.time() - hover_time) / 0.8)
                            cv2.ellipse(frame, (ix, iy), (22, 22), 0, 0, int(prog * 360), (0, 255, 0), 3)
                            if prog >= 1.0:
                                if has_pyautogui: pyautogui.click(_pause=False)
                                iot.send('MOUSE_CLICK')
                                device_state['action'] = 'Click Triggered'
                                hover_time = None
                        else:
                            hover_time = time.time()
                            last_x, last_y = ix, iy
                            device_state['action'] = f'Moving'
                        cv2.circle(frame, (ix, iy), 8, (255, 255, 0), cv2.FILLED)
            else:
                device_state['action'] = 'Searching Hand'

            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
