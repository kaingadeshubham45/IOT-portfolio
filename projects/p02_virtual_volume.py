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
device_state = {'status': 'Active'}

def generate_frames():
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if res.multi_hand_landmarks:
                for hlms in res.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hlms, mp_hands.HAND_CONNECTIONS)
                    lms = hlms.landmark
                    x1, y1 = int(lms[4].x * w), int(lms[4].y * h)
                    x2, y2 = int(lms[8].x * w), int(lms[8].y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    dist = math.hypot(x2 - x1, y2 - y1)
                    vol_pct = int(np.interp(dist, [25, 170], [0, 100]))
                    device_state['volume_level'] = vol_pct
                    iot.send(f'VOL_PWM_{vol_pct}')
                    cv2.putText(frame, f'Vol: {vol_pct}%', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            _, buf = cv2.imencode('.jpg', frame)
            yield (b'--frame
Content-Type: image/jpeg

' + buf.tobytes() + b'
')
    cap.release()
