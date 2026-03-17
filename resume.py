# resume.py
import json
import os
from pathlib import Path
from design import print_error

RESUME_FILE = Path.home() / ".cypher-share-resume.json"

def load_resume_state():
    try:
        if RESUME_FILE.exists():
            with open(RESUME_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print_error(f"Failed to load resume state: {e}", "Continuing without resume.")
    return {}

def save_resume_state(state):
    try:
        with open(RESUME_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print_error(f"Failed to save resume state: {e}")

def clear_resume_state():
    try:
        if RESUME_FILE.exists():
            os.remove(RESUME_FILE)
    except Exception as e:
        print_error(f"Failed to clear resume state: {e}")

def update_progress(file_id, transferred_bytes, total_bytes):
    try:
        state = load_resume_state()
        state[file_id] = {
            "transferred": transferred_bytes,
            "total": total_bytes,
            "timestamp": str(Path(file_id).stat().st_mtime) if Path(file_id).exists() else ""
        }
        save_resume_state(state)
    except Exception as e:
        print_error(f"Failed to update progress: {e}")

def get_resume_info(file_id):
    try:
        state = load_resume_state()
        return state.get(file_id)
    except Exception as e:
        print_error(f"Failed to get resume info: {e}")
        return None