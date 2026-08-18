import os, sys, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot

TITLE = "OCR Text Recognition Scanner"
DESCRIPTION = "Extract printed labels and numbers from live vision stream."
ICON = "📝"
device_state = {'status': 'Active', 'scanned_data': 'Ready for OCR'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 255), 2)
        cv2.putText(frame, "Align Text Region Here", (w//4, h//4 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        _, buf = cv2.imencode('.jpg', frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
