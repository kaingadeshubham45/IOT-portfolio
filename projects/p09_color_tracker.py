import os, sys, cv2, numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot

TITLE = "Object Color Tracking & Sorting"
DESCRIPTION = "HSV color sorting to automate conveyor sorting gates."
ICON = "🎯"
device_state = {'status': 'Active', 'detected_color': 'None'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Orange / Red Object Bounds
        low_red = np.array([0, 120, 70])
        upp_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, low_red, upp_red)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if cnts:
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) > 600:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Target Object", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                device_state['detected_color'] = 'Target Locked'
                iot.send('SERVO_SORT_GATE')
        else:
            device_state['detected_color'] = 'Searching...'

        _, buf = cv2.imencode('.jpg', frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
