import os, sys, math, cv2, time
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
device_state = {'status': 'Active'}

def generate_frames():
    cap = cv2.VideoCapture(0)
    hover_time = None
    last_x, last_y = 0, 0
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
                    lms = hlms.landmark
                    idx_up = lms[8].y < lms[6].y
                    mid_up = lms[12].y < lms[10].y
                    ring_up = lms[16].y < lms[14].y
                    pnk_up = lms[20].y < lms[18].y
                    if idx_up and not mid_up and not ring_up and not pnk_up:
                        ix, iy = int(lms[8].x * w), int(lms[8].y * h)
                        if math.hypot(ix - last_x, iy - last_y) < 15:
                            if hover_time is None:
                                hover_time = time.time()
                            prog = min(1.0, (time.time() - hover_time) / 1.0)
                            cv2.ellipse(frame, (ix, iy), (20, 20), 0, 0, int(prog * 360), (0, 255, 0), 3)
                            if prog >= 1.0:
                                iot.send('MOUSE_CLICK')
                                device_state['action'] = 'Click'
                                hover_time = None
                        else:
                            hover_time = time.time()
                            last_x, last_y = ix, iy
                            device_state['action'] = 'Moving'
                        cv2.circle(frame, (ix, iy), 8, (255, 255, 0), -1)
            _, buf = cv2.imencode('.jpg', frame)
            yield (b'--frame
Content-Type: image/jpeg

' + buf.tobytes() + b'
')
    cap.release()
