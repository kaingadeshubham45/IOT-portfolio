import os, sys, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Finger Counter & Relay Controller"
DESCRIPTION = "Trigger multi-channel IoT relays by counting extended fingers."
ICON = "🖐️"
device_state = {'status': 'Active', 'count': 0, 'relay_triggered': 'Relay 0'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    tip_ids = [4, 8, 12, 16, 20]

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)
            cnt = 0

            if res.multi_hand_landmarks:
                for hlms in res.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hlms, mp_hands.HAND_CONNECTIONS)
                    lms = hlms.landmark
                    fingers = []
                    # Thumb
                    fingers.append(1 if lms[tip_ids[0]].x < lms[tip_ids[0] - 1].x else 0)
                    # 4 fingers
                    for id in range(1, 5):
                        fingers.append(1 if lms[tip_ids[id]].y < lms[tip_ids[id] - 2].y else 0)
                    cnt = sum(fingers)
                    device_state['count'] = cnt
                    device_state['relay_triggered'] = f'Relay {cnt}'
                    iot.send(f'RELAY_{cnt}_ON')

            cv2.rectangle(frame, (20, 20), (160, 100), (0, 200, 0), cv2.FILLED)
            cv2.putText(frame, f"{cnt}", (70, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
