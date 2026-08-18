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

TITLE = "Virtual Keyboard Automation"
DESCRIPTION = "Touchless interactive on-screen key typing with distance tap detection."
ICON = "⌨️"
device_state = {'status': 'Active', 'last_key': 'None', 'typed_text': ''}
KEYS = [["Q", "W", "E", "R", "T"], ["A", "S", "D", "F", "G"], ["Z", "X", "C", "V", "B"]]

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    last_press = 0
    text_buffer = ""

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            # Draw virtual keys
            for r_idx, row in enumerate(KEYS):
                for c_idx, key in enumerate(row):
                    kx, ky = 50 + c_idx * 70, 50 + r_idx * 70
                    cv2.rectangle(frame, (kx, ky), (kx + 60, ky + 60), (255, 0, 0), cv2.FILLED)
                    cv2.putText(frame, key, (kx + 20, ky + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            if res.multi_hand_landmarks:
                for hlms in res.multi_hand_landmarks:
                    lms = hlms.landmark
                    ix, iy = int(lms[8].x * w), int(lms[8].y * h)
                    tx, ty = int(lms[4].x * w), int(lms[4].y * h)
                    cv2.circle(frame, (ix, iy), 6, (0, 255, 255), cv2.FILLED)

                    dist = math.hypot(ix - tx, iy - ty)
                    if dist < 30 and (time.time() - last_press > 0.6):
                        for r_idx, row in enumerate(KEYS):
                            for c_idx, key in enumerate(row):
                                kx, ky = 50 + c_idx * 70, 50 + r_idx * 70
                                if kx < ix < kx + 60 and ky < iy < ky + 60:
                                    cv2.rectangle(frame, (kx, ky), (kx + 60, ky + 60), (0, 255, 0), cv2.FILLED)
                                    text_buffer += key
                                    device_state['last_key'] = key
                                    device_state['typed_text'] = text_buffer[-15:]
                                    iot.send(f'KEY_{key}')
                                    last_press = time.time()

            cv2.putText(frame, f"Text: {text_buffer[-10:]}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
