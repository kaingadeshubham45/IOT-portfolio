import os
import sys
import importlib
from flask import Flask, render_template, Response, jsonify

# Ensure root directory is always discoverable by all sub-modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

app = Flask(__name__)
PROJECTS_DIR = "projects"

def get_available_projects():
    projects = []
    if not os.path.exists(PROJECTS_DIR):
        return projects

    for filename in sorted(os.listdir(PROJECTS_DIR)):
        if filename.endswith(".py") and not filename.startswith("__"):
            mod_name = filename[:-3]
            try:
                mod = importlib.import_module(f"{PROJECTS_DIR}.{mod_name}")
                projects.append({
                    "id": mod_name,
                    "title": getattr(mod, "TITLE", mod_name.replace("_", " ").title()),
                    "description": getattr(mod, "DESCRIPTION", "OpenCV + MediaPipe Automation"),
                    "icon": getattr(mod, "ICON", "⚡")
                })
            except Exception as e:
                print(f"[Import Error] Failed to load {mod_name}: {e}")
    return projects

@app.route('/')
def home():
    return render_template('index.html', projects=get_available_projects())

@app.route('/project/<project_id>')
def view_project(project_id):
    try:
        mod = importlib.import_module(f"{PROJECTS_DIR}.{project_id}")
        title = getattr(mod, "TITLE", project_id)
        desc = getattr(mod, "DESCRIPTION", "")
        return render_template('project_view.html', project_id=project_id, title=title, desc=desc)
    except ModuleNotFoundError:
        return "Project not found", 404

@app.route('/video_feed/<project_id>')
def video_feed(project_id):
    try:
        mod = importlib.import_module(f"{PROJECTS_DIR}.{project_id}")
        return Response(mod.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        return f"Stream error: {e}", 500

@app.route('/api/status/<project_id>')
def get_status(project_id):
    try:
        mod = importlib.import_module(f"{PROJECTS_DIR}.{project_id}")
        status = getattr(mod, "device_state", {"status": "Active"})
        return jsonify(status)
    except Exception:
        return jsonify({"status": "Offline"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)