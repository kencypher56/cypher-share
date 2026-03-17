#!/usr/bin/env python3
"""
Cypher-Share Environment Setup
Automatically installs Miniconda (if missing) and creates a dedicated conda environment.
Run with: python setup.py
"""

import os
import sys
import subprocess
import platform
import urllib.request
import tempfile
import shutil
import time

# --- Frankenstein-themed messages ---
def print_step(msg):
    print(f"[🧪] {msg}")

def print_success(msg):
    print(f"[✅] {msg}")

def print_error(msg):
    print(f"[💀] ERROR: {msg}")

def print_warning(msg):
    print(f"[⚠️] {msg}")

# --- Platform detection ---
system = platform.system().lower()
arch = platform.machine().lower()

# Map architecture to Miniconda installer filename
if system == "linux":
    if "x86_64" in arch:
        installer = "Miniconda3-latest-Linux-x86_64.sh"
    elif "aarch64" in arch:
        installer = "Miniconda3-latest-Linux-aarch64.sh"
    else:
        print_error(f"Unsupported architecture: {arch}")
        sys.exit(1)
    installer_url = f"https://repo.anaconda.com/miniconda/{installer}"
elif system == "darwin":
    if "arm64" in arch:
        installer = "Miniconda3-latest-MacOSX-arm64.sh"
    else:
        installer = "Miniconda3-latest-MacOSX-x86_64.sh"
    installer_url = f"https://repo.anaconda.com/miniconda/{installer}"
elif system == "windows":
    if "64" in arch:
        installer = "Miniconda3-latest-Windows-x86_64.exe"
    else:
        installer = "Miniconda3-latest-Windows-x86.exe"
    installer_url = f"https://repo.anaconda.com/miniconda/{installer}"
else:
    print_error(f"Unsupported OS: {system}")
    sys.exit(1)

# --- Helper functions ---
def run_cmd(cmd, shell=True, capture=False):
    """Run a command and return output if capture=True."""
    if capture:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    else:
        return subprocess.run(cmd, shell=shell).returncode

def is_conda_available():
    """Check if conda command is available."""
    code, out, _ = run_cmd("conda --version", capture=True)
    return code == 0

def get_conda_base():
    """Get conda base directory."""
    code, out, _ = run_cmd("conda info --base", capture=True)
    if code == 0:
        return out
    return None

def install_miniconda():
    """Download and install Miniconda silently."""
    print_step(f"Miniconda not found. Downloading installer for {system}...")
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    installer_path = os.path.join(temp_dir, installer)

    # Download with progress
    try:
        urllib.request.urlretrieve(installer_url, installer_path)
    except Exception as e:
        print_error(f"Download failed: {e}")
        shutil.rmtree(temp_dir)
        sys.exit(1)

    print_step("Installing Miniconda (this may take a few minutes)...")
    install_prefix = os.path.expanduser("~/miniconda3")
    if system == "windows":
        # Windows silent install
        cmd = f'start /wait "" "{installer_path}" /InstallationType=JustMe /RegisterPython=0 /S /D={install_prefix}'
        run_cmd(cmd)
    else:
        # Unix: run installer in batch mode
        os.chmod(installer_path, 0o755)
        cmd = f'"{installer_path}" -b -p "{install_prefix}"'
        run_cmd(cmd)

    # Cleanup
    shutil.rmtree(temp_dir)

    # Add conda to PATH for this script
    if system == "windows":
        conda_bin = os.path.join(install_prefix, "Scripts", "conda.exe")
        os.environ["PATH"] = os.path.join(install_prefix, "Scripts") + os.pathsep + os.environ["PATH"]
        os.environ["PATH"] = os.path.join(install_prefix, "Library", "bin") + os.pathsep + os.environ["PATH"]
    else:
        conda_bin = os.path.join(install_prefix, "bin", "conda")
        os.environ["PATH"] = os.path.join(install_prefix, "bin") + os.pathsep + os.environ["PATH"]

    # Verify installation
    if not os.path.exists(conda_bin):
        print_error("Conda installation failed.")
        sys.exit(1)

    print_success("Miniconda installed successfully.")

def create_conda_env():
    """Create cypher-share environment with Python 3.11 and install dependencies."""
    env_name = "cypher-share"
    python_version = "3.11"

    # Check if environment already exists
    code, out, _ = run_cmd(f"conda env list | grep {env_name}", capture=True)
    if code == 0:
        print_warning(f"Environment '{env_name}' already exists. Updating dependencies...")
        # Just install dependencies
        cmd = f'conda run -n {env_name} pip install -r requirements.txt'
        ret = run_cmd(cmd)
        if ret == 0:
            print_success(f"Dependencies updated in '{env_name}'.")
        else:
            print_error("Failed to install dependencies.")
            sys.exit(1)
    else:
        print_step(f"Creating conda environment '{env_name}' with Python {python_version}...")
        cmd = f'conda create -n {env_name} python={python_version} -y'
        ret = run_cmd(cmd)
        if ret != 0:
            print_error("Failed to create conda environment.")
            sys.exit(1)

        print_step("Installing dependencies from requirements.txt...")
        cmd = f'conda run -n {env_name} pip install -r requirements.txt'
        ret = run_cmd(cmd)
        if ret != 0:
            print_error("Failed to install dependencies.")
            sys.exit(1)

        print_success(f"Environment '{env_name}' created and dependencies installed.")

def print_activation_instructions():
    """Show how to activate the environment."""
    if system == "windows":
        activate_cmd = "conda activate cypher-share"
    else:
        activate_cmd = "conda activate cypher-share"
    print("\n" + "="*60)
    print("🎉 All done! To start using Cypher-Share, activate the environment:")
    print(f"\n   [bold green]conda activate cypher-share[/]\n")
    print("Then run: python run.py")
    print("="*60)

# --- Main ---
def main():
    print("""
    ╔══════════════════════════════════╗
    ║   Cypher-Share Environment Setup ║
    ╚══════════════════════════════════╝
    """)

    # Check if we should use conda or venv (user choice)
    choice = input("Use [1] conda (recommended) or [2] venv? (1/2): ").strip()
    if choice == "2":
        # Fallback to venv (original setup.py code)
        print_step("Setting up virtual environment (venv)...")
        run_cmd(f"{sys.executable} -m venv venv")
        pip_cmd = "venv\\Scripts\\pip" if system == "windows" else "venv/bin/pip"
        run_cmd(f"{pip_cmd} install --upgrade pip")
        run_cmd(f"{pip_cmd} install -r requirements.txt")
        activate = "venv\\Scripts\\activate" if system == "windows" else "source venv/bin/activate"
        print(f"\n[✓] Virtual env ready. Activate with: {activate}")
        return

    # Conda path
    if not is_conda_available():
        print_warning("Conda is not installed on your system.")
        install = input("Do you want to download and install Miniconda now? (y/n): ").strip().lower()
        if install == 'y':
            install_miniconda()
        else:
            print_error("Conda is required for this setup. Exiting.")
            sys.exit(1)

    # Now conda should be available
    if not is_conda_available():
        print_error("Conda still not found after installation. Please add it to your PATH manually.")
        sys.exit(1)

    create_conda_env()
    print_activation_instructions()

if __name__ == "__main__":
    main()