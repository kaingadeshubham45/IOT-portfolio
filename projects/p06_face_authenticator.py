import os, sys, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot

TITLE = "Face Recognition Door Lock"
DESCRIPTION = "IoT solenoid door unlock via facial biometric confirmation."
ICON = "🔓"
device_state = {'status': 'Active', 'door_state': 'LOCKED', 'auth': 'Scanning'}
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "AUTHORIZED USER", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            device_state['door_state'] = 'UNLOCKED'
            device_state['auth'] = 'Access Granted'
            iot.send('DOOR_UNLOCK')
        else:
            device_state['door_state'] = 'LOCKED'
            device_state['auth'] = 'Scanning...'

        _, buf = cv2.imencode('.jpg', frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
