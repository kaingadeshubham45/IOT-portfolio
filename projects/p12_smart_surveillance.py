import os, sys, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot

TITLE = "Smart Security Surveillance"
DESCRIPTION = "Motion detection security trigger with snapshot alerts."
ICON = "🚨"
device_state = {'status': 'Armed', 'security_event': 'Secure'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    first_frame = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if first_frame is None:
            first_frame = gray
            continue

        frame_delta = cv2.absdiff(first_frame, gray)
        thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion = False
        for c in cnts:
            if cv2.contourArea(c) > 1200:
                motion = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        if motion:
            device_state['security_event'] = 'MOTION DETECTED!'
            cv2.putText(frame, "SECURITY ALERT", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            iot.send('ALERT_TRIGGER')
        else:
            device_state['security_event'] = 'Monitoring Clear'

        _, buf = cv2.imencode('.jpg', frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
