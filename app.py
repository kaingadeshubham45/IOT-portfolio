import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

PROJECTS = {
    'p01_virtual_mouse': {
        'id': 'p01_virtual_mouse',
        'title': 'Virtual Mouse Control',
        'desc': 'Navigate cursor with index finger; left-click via thumb-index pinch gesture.',
        'icon': '🖱️'
    },
    'p02_virtual_volume': {
        'id': 'p02_virtual_volume',
        'title': 'Virtual Volume Control',
        'desc': 'Logarithmic audio gain modulation via vertical hand elevation.',
        'icon': '🔊'
    },
    'p03_virtual_brightness': {
        'id': 'p03_virtual_brightness',
        'title': 'Virtual Brightness Control',
        'desc': 'Adjust display luminosity and backlight levels using pinch distance metrics.',
        'icon': '☀️'
    },
    'p04_finger_counter': {
        'id': 'p04_finger_counter',
        'title': 'Finger Counter & Showcase',
        'desc': 'Vector landmark tracking detecting extended finger count from 1 to 5.',
        'icon': '🖐️'
    },
    'p05_rock_paper_scissors': {
        'id': 'p05_rock_paper_scissors',
        'title': 'Rock Paper Scissors AI',
        'desc': 'Interactive hand gesture showdown playing against an automated AI engine.',
        'icon': '✊'
    },
    'p06_face_attendance': {
        'id': 'p06_face_attendance',
        'title': 'Face Attendance System',
        'desc': 'Biometric facial validation with automated attendance logging (Date & Time).',
        'icon': '📋'
    },
    'p07_face_mask_detector': {
        'id': 'p07_face_mask_detector',
        'title': 'Face Mask Detection',
        'desc': 'Facial occlusion analysis verifying mask compliance for safety protocols.',
        'icon': '😷'
    },
    'p08_drowsiness_detector': {
        'id': 'p08_drowsiness_detector',
        'title': 'Drowsiness Face Detection',
        'desc': 'Eye Aspect Ratio (EAR) monitoring triggering real-time buzzer alarms.',
        'icon': '⚠️'
    },
    'p09_virtual_drawing': {
        'id': 'p09_virtual_drawing',
        'title': 'Virtual Drawing Board',
        'desc': 'In-air touchless digital canvas drawing via index finger tracking.',
        'icon': '🎨'
    },
    'p10_presentation_control': {
        'id': 'p10_presentation_control',
        'title': 'Gesture Presentation Control',
        'desc': 'Slide deck navigation using touchless directional swipe gestures.',
        'icon': '📊'
    },
    'p11_media_player': {
        'id': 'p11_media_player',
        'title': 'Gesture Media Player',
        'desc': 'Play, pause, skip, and rewind media controls via hand gestures.',
        'icon': '🎬'
    },
    'p12_sign_language': {
        'id': 'p12_sign_language',
        'title': 'AI Sign Language Recognition',
        'desc': 'Real-time classification of standard sign language hand alphabet gestures.',
        'icon': '🤟'
    }
}

@app.route('/')
def index():
    return render_template('index.html', projects=PROJECTS)

@app.route('/project/<project_id>')
def view_project(project_id):
    proj = PROJECTS.get(project_id)
    if not proj:
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