import os
import sys
import importlib
import glob
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_PROJECTS = {
    'p01_virtual_mouse': {'title': 'Virtual Mouse Control', 'desc': 'Cursor navigation via index finger and dwell hover-click.', 'icon': '🖱️'},
    'p02_virtual_volume': {'title': 'Virtual Volume Control', 'desc': 'Adjust master audio and send PWM output based on pinch distance.', 'icon': '🔊'},
    'p03_virtual_keyboard': {'title': 'Virtual Keyboard Automation', 'desc': 'Key press detection via finger tap tracking.', 'icon': '⌨️'},
    'p04_finger_counter': {'title': 'Finger Counter & Relay Controller', 'desc': 'Trigger multi-channel IoT relays by counting fingers.', 'icon': '🖐️'},
    'p05_presentation_controller': {'title': 'Hand Gesture Presentation Control', 'desc': 'Slide deck navigation using left/right swipe gestures.', 'icon': '📊'},
    'p06_face_authenticator': {'title': 'Face Recognition Door Lock', 'desc': 'IoT solenoid door unlock via facial match confirmation.', 'icon': '🔓'},
    'p07_drowsiness_detector': {'title': 'Driver Drowsiness Alert System', 'desc': 'Detect eye closure rates and trigger buzzer alerts.', 'icon': '⚠️'},
    'p08_pose_tracker': {'title': 'AI Posture Trainer', 'desc': 'Real-time spine angle posture correction tracker.', 'icon': '🧘'},
    'p09_color_tracker': {'title': 'Object Color Tracking & Sorting', 'desc': 'HSV color sorting to automate conveyor gates.', 'icon': '🎯'},
    'p10_optical_character': {'title': 'OCR Text Recognition Scanner', 'desc': 'Text extraction from live video feed display.', 'icon': '📝'},
    'p11_qr_scanner': {'title': 'Smart QR Access Gate', 'desc': 'Scan QR codes to authorize IoT barrier gate access.', 'icon': '📱'},
    'p12_smart_surveillance': {'title': 'Smart Security Surveillance', 'desc': 'Motion detection security trigger with snapshot alerts.', 'icon': '🚨'}
}

PROJECTS = {}

for p_id, meta in DEFAULT_PROJECTS.items():
    mod = None
    try:
        mod = importlib.import_module(f'projects.{p_id}')
    except Exception as e:
        print(f"Fallback active for {p_id}: {e}")
        
    PROJECTS[p_id] = {
        'id': p_id,
        'title': getattr(mod, 'TITLE', meta['title']) if mod else meta['title'],
        'desc': getattr(mod, 'DESCRIPTION', meta['desc']) if mod else meta['desc'],
        'icon': getattr(mod, 'ICON', meta['icon']) if mod else meta['icon'],
        'module': mod
    }

@app.route('/')
def index():
    return render_template('index.html', projects=PROJECTS)

@app.route('/project/<project_id>')
def view_project(project_id):
    proj = PROJECTS.get(project_id)
    if not proj:
        return "Project Not Found", 404
    return render_template('project.html', project=proj)

@app.route('/video_feed/<project_id>')
def video_feed(project_id):
    proj = PROJECTS.get(project_id)
    if proj and proj['module'] and hasattr(proj['module'], 'generate_frames'):
        return Response(proj['module'].generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera Stream Unavailable", 404

@app.route('/api/state/<project_id>')
def get_state(project_id):
    proj = PROJECTS.get(project_id)
    if proj and proj['module'] and hasattr(proj['module'], 'device_state'):
        return jsonify(proj['module'].device_state)
    return jsonify({'status': 'Active'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
