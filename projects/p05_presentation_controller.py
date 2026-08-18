import os, sys, time, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Hand Gesture Presentation Control"
DESCRIPTION = "Slide deck navigation using left/right swipe gestures."
ICON = "📊"
device_state = {'status': 'Active', 'current_slide': 1, 'last_action': 'None'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    prev_x = None
    last_swipe = time.time()
    slide = 1

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
                    cx = int(hlms.landmark[9].x * w)
                    if prev_x is not None and (time.time() - last_swipe > 1.0):
                        diff = cx - prev_x
                        if diff > 90:
                            slide += 1
                            device_state['last_action'] = 'Next Slide (Swipe Right)'
                            device_state['current_slide'] = slide
                            iot.send('SLIDE_NEXT')
                            last_swipe = time.time()
                        elif diff < -90:
                            slide = max(1, slide - 1)
                            device_state['last_action'] = 'Prev Slide (Swipe Left)'
                            device_state['current_slide'] = slide
                            iot.send('SLIDE_PREV')
                            last_swipe = time.time()
                    prev_x = cx
            else:
                prev_x = None

            cv2.putText(frame, f"Slide: {slide}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, device_state['last_action'], (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
