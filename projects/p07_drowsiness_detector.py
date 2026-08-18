import os, sys, time, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_face = mp.solutions.face_mesh
except AttributeError:
    import mediapipe.python.solutions.face_mesh as mp_face

TITLE = "Driver Drowsiness Alert System"
DESCRIPTION = "Detect eye closure rates and trigger buzzer alerts."
ICON = "⚠️"
device_state = {'status': 'Active', 'alert': 'Normal'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    closed_start = None

    with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True) as mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = mesh.process(rgb)

            if res.multi_face_landmarks:
                for flms in res.multi_face_landmarks:
                    lms = flms.landmark
                    # Left eye top/bottom
                    p1 = (int(lms[159].x * w), int(lms[159].y * h))
                    p2 = (int(lms[145].x * w), int(lms[145].y * h))
                    eye_dist = abs(p1[1] - p2[1])

                    if eye_dist < 6:
                        if closed_start is None: closed_start = time.time()
                        if time.time() - closed_start > 1.2:
                            cv2.putText(frame, "DROWSINESS ALERT!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                            device_state['alert'] = 'DANGER: SLEEP DETECTED'
                            iot.send('BUZZER_ALARM_ON')
                    else:
                        closed_start = None
                        device_state['alert'] = 'Normal Driver State'
                        iot.send('BUZZER_OFF')

            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
