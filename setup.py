import os
import subprocess
import sys
import venv
from pathlib import Path

APP_NAME = "milibots-panel"
SERVICE_NAME = f"{APP_NAME}.service"
APP_DIR = Path(__file__).parent.resolve()
VENV_DIR = APP_DIR / "venv"
PYTHON_PATH = VENV_DIR / "bin" / "python"
GUNICORN_PATH = VENV_DIR / "bin" / "gunicorn"
REQUIREMENTS_FILE = APP_DIR / "requirements.txt"
SERVICE_FILE_PATH = Path(f"/etc/systemd/system/{SERVICE_NAME}")

SERVICE_TEMPLATE = f"""[Unit]
Description=MiliBots Admin Panel
After=network.target

[Service]
WorkingDirectory={APP_DIR}
ExecStart={GUNICORN_PATH} -w 2 -b 0.0.0.0:7878 app:app
Restart=always
RestartSec=5
Environment="PATH={VENV_DIR}/bin"

[Install]
WantedBy=multi-user.target
"""

def run(cmd: list, check=True):
    """Helper to run system commands safely."""
    print(f"➡️ Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"⚠️ Error running {' '.join(cmd)}:\n{result.stderr}")
        if check:
            sys.exit(result.returncode)
    return result


def ensure_venv():
    """Create venv if not already present."""
    if not VENV_DIR.exists():
        print("📦 Creating virtual environment...")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    else:
        print("✅ Virtual environment already exists.")


def install_requirements():
    """Install packages from requirements.txt."""
    print("📥 Installing required packages...")
    run([PYTHON_PATH, "-m", "pip", "install", "--upgrade", "pip"])
    run([PYTHON_PATH, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def create_systemd_service():
    """Generate systemd service file if not exists."""
    if SERVICE_FILE_PATH.exists():
        print(f"✅ Service file already exists at {SERVICE_FILE_PATH}")
        return

    print(f"🧾 Creating systemd service at {SERVICE_FILE_PATH}...")
    with open(SERVICE_FILE_PATH, "w") as f:
        f.write(SERVICE_TEMPLATE)

    run(["sudo", "systemctl", "daemon-reload"])
    run(["sudo", "systemctl", "enable", SERVICE_NAME])
    print("✅ Systemd service created and enabled.")


def start_service():
    """Start or restart the service."""
    print("🚀 Starting the service...")
    run(["sudo", "systemctl", "restart", SERVICE_NAME], check=False)
    status = run(["systemctl", "is-active", SERVICE_NAME], check=False)
    if "active" in status.stdout:
        print("✅ Service is running successfully.")
    else:
        print("⚠️ Service may not have started correctly. Check logs using:")
        print(f"   sudo journalctl -u {SERVICE_NAME} -f")


def main():
    print(f"🔧 Setting up {APP_NAME}...")
    ensure_venv()
    install_requirements()
    create_systemd_service()
    start_service()
    print("🎉 Setup complete!")


if __name__ == "__main__":
    main()
