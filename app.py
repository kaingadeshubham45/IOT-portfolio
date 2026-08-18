import os, sys, importlib, glob
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROJECTS = {}
projects_dir = os.path.join(BASE_DIR, 'projects')

for filepath in sorted(glob.glob(os.path.join(projects_dir, 'p*.py'))):
    mod_name = os.path.splitext(os.path.basename(filepath))[0]
    try:
        module = importlib.import_module(f'projects.{mod_name}')
        PROJECTS[mod_name] = {
            'id': mod_name,
            'title': getattr(module, 'TITLE', mod_name.replace('_', ' ').title()),
            'desc': getattr(module, 'DESCRIPTION', 'Vision & IoT project module.'),
            'icon': getattr(module, 'ICON', '⚡'),
            'module': module
        }
        print(f"[SUCCESS] Loaded: {mod_name}")
    except Exception as e:
        print(f"[ERROR] Loading {mod_name}: {e}")

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
    if proj and proj.get('module') and hasattr(proj['module'], 'generate_frames'):
        return Response(proj['module'].generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera Stream Unavailable", 404

@app.route('/api/state/<project_id>')
def get_state(project_id):
    proj = PROJECTS.get(project_id)
    if proj and proj.get('module') and hasattr(proj['module'], 'device_state'):
        return jsonify(proj['module'].device_state)
    return jsonify({'status': 'Active'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
