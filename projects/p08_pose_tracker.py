import os, sys, math, cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from iot_bridge import iot
import mediapipe as mp

try:
    mp_pose = mp.solutions.pose
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.pose as mp_pose
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "AI Posture Trainer"
DESCRIPTION = "Real-time spine angle posture correction tracker."
ICON = "🧘"
device_state = {'status': 'Active', 'posture': 'Good'}

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(0)
    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            if res.pose_landmarks:
                mp_draw.draw_landmarks(frame, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                lms = res.pose_landmarks.landmark
                ear = (int(lms[7].x * w), int(lms[7].y * h))
                shldr = (int(lms[11].x * w), int(lms[11].y * h))
                angle = abs(math.degrees(math.atan2(shldr[1] - ear[1], shldr[0] - ear[0])))

                if angle < 75 or angle > 105:
                    cv2.putText(frame, "POOR POSTURE: Sit Straight", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    device_state['posture'] = 'SLOUCHING'
                    iot.send('HAPTIC_WARN')
                else:
                    cv2.putText(frame, "POSTURE: Good", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    device_state['posture'] = 'CORRECT'

            _, buf = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
    cap.release()
