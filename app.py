import os
import sys
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Complete catalog of all 12 projects with full metadata
PROJECTS = {
    'p01_virtual_mouse': {
        'id': 'p01_virtual_mouse',
        'title': 'Virtual Mouse Control',
        'desc': 'Direct index-finger cursor tracking and auto-hover click.',
        'icon': '🖱️'
    },
    'p02_virtual_volume': {
        'id': 'p02_virtual_volume',
        'title': 'Virtual Volume Control',
        'desc': 'Adjust master audio and send PWM output based on finger gestures.',
        'icon': '🔊'
    },
    'p03_virtual_keyboard': {
        'id': 'p03_virtual_keyboard',
        'title': 'Virtual Keyboard Automation',
        'desc': 'Touchless interactive on-screen key typing with distance tap detection.',
        'icon': '⌨️'
    },
    'p04_finger_counter': {
        'id': 'p04_finger_counter',
        'title': 'Finger Counter & Relay Controller',
        'desc': 'Trigger multi-channel IoT relays by counting extended fingers.',
        'icon': '🖐️'
    },
    'p05_presentation_controller': {
        'id': 'p05_presentation_controller',
        'title': 'Hand Gesture Presentation Control',
        'desc': 'Slide deck navigation using left/right swipe gestures.',
        'icon': '📊'
    },
    'p06_face_authenticator': {
        'id': 'p06_face_authenticator',
        'title': 'Face Recognition Door Lock',
        'desc': 'IoT solenoid door unlock via facial biometric confirmation.',
        'icon': '🔓'
    },
    'p07_drowsiness_detector': {
        'id': 'p07_drowsiness_detector',
        'title': 'Driver Drowsiness Alert System',
        'desc': 'Detect eye closure rates and trigger buzzer alerts.',
        'icon': '⚠️'
    },
    'p08_pose_tracker': {
        'id': 'p08_pose_tracker',
        'title': 'AI Posture Trainer',
        'desc': 'Real-time spine angle posture correction tracker.',
        'icon': '🧘'
    },
    'p09_color_tracker': {
        'id': 'p09_color_tracker',
        'title': 'Object Color Tracking & Sorting',
        'desc': 'HSV color sorting to automate conveyor sorting gates.',
        'icon': '🎯'
    },
    'p10_optical_character': {
        'id': 'p10_optical_character',
        'title': 'OCR Text Recognition Scanner',
        'desc': 'Extract printed labels and numbers from live vision stream.',
        'icon': '📝'
    },
    'p11_qr_scanner': {
        'id': 'p11_qr_scanner',
        'title': 'Smart QR Access Gate',
        'desc': 'Scan QR codes to authorize IoT barrier gate access.',
        'icon': '📱'
    },
    'p12_smart_surveillance': {
        'id': 'p12_smart_surveillance',
        'title': 'Smart Security Surveillance',
        'desc': 'Motion detection security trigger with snapshot alerts.',
        'icon': '🚨'
    }
}

@app.route('/')
def index():
    return render_template('index.html', projects=PROJECTS)

@app.route('/project/<project_id>')
def view_project(project_id):
    proj = PROJECTS.get(project_id)
    if not proj:
        # Match shorthand keys if accessed like 'p01'
        for k, v in PROJECTS.items():
            if k.startswith(project_id) or project_id.startswith(k):
                proj = v
                break
    if not proj:
        return "Project Not Found", 404
    return render_template('project.html', project=proj)

@app.route('/api/state/<project_id>')
def get_state(project_id):
    return jsonify({'status': 'Online', 'mode': 'Browser Vision Engine'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)