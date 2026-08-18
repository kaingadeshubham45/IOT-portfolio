import os, sys, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot

TITLE = "Smart QR Access Gate"
DESCRIPTION = "Scan QR codes to authorize IoT barrier gate access."
ICON = "📱"
device_state = {'status': 'Active', 'payload': 'No QR code'}
detector = cv2.QRCodeDetector()

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            device_state['payload'] = data
            cv2.putText(frame, f"QR: {data}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            iot.send(f'GATE_AUTH_{data}')

        _, buf = cv2.imencode('.jpg', frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
