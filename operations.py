# operations.py
import os
from pathlib import Path
from design import print_error

def get_files_and_size(paths):
    file_list = []
    total_size = 0
    for p in paths:
        p = Path(p).expanduser().resolve()
        if not p.exists():
            print_error(f"Path does not exist: {p}", "Check the path and try again.")
            continue
        try:
            if p.is_file():
                rel = p.name
                size = p.stat().st_size
                file_list.append((rel, p, size))
                total_size += size
            elif p.is_dir():
                root_len = len(p.parts)
                for root, _, files in os.walk(p):
                    for f in files:
                        full = Path(root) / f
                        rel = str(Path(*full.parts[root_len:]))
                        size = full.stat().st_size
                        file_list.append((rel, full, size))
                        total_size += size
        except PermissionError:
            print_error(f"Permission denied: {p}", "Try running with appropriate privileges.")
        except Exception as e:
            print_error(f"Error accessing {p}: {e}")
    return file_list, total_size

def ensure_output_dir():
    out_dir = Path.home() / "Desktop" / "cypher-share"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print_error(f"Cannot create output directory: {e}", "Check disk space and permissions.")
        raise
    return out_dir

def human_readable_size(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"