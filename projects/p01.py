import os
import sys
import time
import math
import cv2

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from iot_bridge import iot

import mediapipe as mp
try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    import mediapipe.python.solutions.hands as mp_hands
    import mediapipe.python.solutions.drawing_utils as mp_draw

TITLE = "Virtual Mouse Control"
DESCRIPTION = "Single index finger tracking with hover-to-click dwell detection."
ICON = "🖱️"

device_state = {"action": "Neutral", "click": False, "dwell_progress": 0}

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    screen_w, screen_h = pyautogui.size()
    has_pyautogui = True
except Exception:
    has_pyautogui = False
    screen_w, screen_h = 1920, 1080

def generate_frames():
    cap = cv2.VideoCapture(0)
    
    hover_start_time = None
    last_x, last_y = 0, 0
    dwell_threshold = 1.0  # seconds to hold steady for click
    movement_tolerance = 15  # pixels

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_lms in results.multi_hand_landmarks:
                    lms = hand_lms.landmark

                    # Finger states: Tip higher than PIP joint means extended
                    index_up = lms[8].y < lms[6].y
                    middle_up = lms[12].y < lms[10].y
                    ring_up = lms[16].y < lms[14].y
                    pinky_up = lms[20].y < lms[18].y

                    # STRICT: ONLY Index Finger must be extended
                    if index_up and not middle_up and not ring_up and not pinky_up:
                        ix, iy = int(lms[8].x * w), int(lms[8].y * h)
                        
                        # Move OS Cursor
                        if has_pyautogui:
                            cursor_x = screen_w / w * ix
                            cursor_y = screen_h / h * iy
                            pyautogui.moveTo(cursor_x, cursor_y, _pause=False)

                        # Dwell / Hover-to-Click calculation
                        dist_moved = math.hypot(ix - last_x, iy - last_y)
                        
                        if dist_moved < movement_tolerance:
                            if hover_start_time is None:
                                hover_start_time = time.time()
                            
                            elapsed = time.time() - hover_start_time
                            progress = min(1.0, elapsed / dwell_threshold)
                            device_state["dwell_progress"] = int(progress * 100)

                            # Draw circular progress bar around fingertip
                            angle = int(progress * 360)
                            cv2.ellipse(frame, (ix, iy), (22, 22), 0, 0, angle, (0, 255, 0), 3)

                            if progress >= 1.0:
                                if has_pyautogui:
                                    pyautogui.click(_pause=False)
                                device_state["action"] = "Left Click (Dwell)"
                                device_state["click"] = True
                                iot.send("MOUSE_CLICK")
                                cv2.circle(frame, (ix, iy), 18, (0, 0, 255), cv2.FILLED)
                                hover_start_time = None  # Reset after click
                            else:
                                device_state["action"] = f"Holding ({int(progress*100)}%)"
                                device_state["click"] = False
                        else:
                            # Reset timer when finger moves beyond threshold
                            hover_start_time = time.time()
                            last_x, last_y = ix, iy
                            device_state["action"] = "Moving Cursor"
                            device_state["click"] = False

                        cv2.circle(frame, (ix, iy), 8, (255, 255, 0), cv2.FILLED)

                    else:
                        hover_start_time = None
                        device_state["action"] = "Ignored (Show Only Index Finger)"
                        device_state["click"] = False
                        cv2.putText(frame, "Show ONLY Index Finger", (20, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    cap.release()