import os
import subprocess
import sys
from pathlib import Path
import typer

smtp_app = typer.Typer()

VENV_DIR = Path.home() / ".evrmail" / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
SMTP_SCRIPT = Path(__file__).resolve().parent / "smtp_server.py"
SMTP_LOG_FILE = Path.home() / ".evrmail" / "smtp.log"
SYSTEMD_UNIT_PATH = Path.home() / ".config/systemd/user/evrmail-fastapi.service"
UNIT_NAME = "evrmail-fastapi"

def ensure_venv():
    if not VENV_PYTHON.exists():
        typer.echo("📦 Creating virtual environment...")
        subprocess.run(["python3", "-m", "venv", str(VENV_DIR)], check=True)
        subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "fastapi", "uvicorn"], check=True)
def write_unit_file():
    SMTP_SCRIPT_FINAL = Path.home() / "Documents" / "Manticore-Technologies" / "Python" / "evmail-dev" / "src" / "evrmail" / "commands" / "smtp_server.py"
    unit = f"""[Unit]
Description=EvrMail FastAPI Server
After=network.target

[Service]
ExecStart={VENV_PYTHON} {SMTP_SCRIPT_FINAL}
WorkingDirectory={SMTP_SCRIPT_FINAL.parent.parent.parent.parent}
Restart=on-failure
RestartSec=10
Environment="PYTHONUNBUFFERED=1"
StandardOutput=append:{SMTP_LOG_FILE}
StandardError=append:{SMTP_LOG_FILE}

[Install]
WantedBy=default.target
"""
    SYSTEMD_UNIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYSTEMD_UNIT_PATH.write_text(unit)
@smtp_app.command("install")
def manual_install():
    typer.echo("📦 Installing EvrMail FastAPI server systemd unit...")
    install_unit()

@smtp_app.command("uninstall")
def uninstall():
    typer.echo("🧼 Uninstalling EvrMail FastAPI server systemd service...")
    subprocess.run(["systemctl", "--user", "stop", UNIT_NAME])
    subprocess.run(["systemctl", "--user", "disable", UNIT_NAME])
    SYSTEMD_UNIT_PATH.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    typer.echo("✅ Uninstalled.")
def install_unit():
    typer.echo("📝 Installing systemd unit...")
    write_unit_file()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", UNIT_NAME], check=True)
    typer.echo("✅ systemd unit installed.")



@smtp_app.command("start")
def start():
    ensure_venv()
    if not SYSTEMD_UNIT_PATH.exists():
        install_unit()
    typer.echo("🚀 Starting EvrMail webhook server...")
    subprocess.run(["systemctl", "--user", "start", UNIT_NAME])

@smtp_app.command("stop")
def stop():
    typer.echo("🛑 Stopping EvrMail webhook server...")
    subprocess.run(["systemctl", "--user", "stop", UNIT_NAME])

@smtp_app.command("restart")
def restart():
    typer.echo("🔁 Restarting EvrMail webhook server...")
    subprocess.run(["systemctl", "--user", "restart", UNIT_NAME])

@smtp_app.command("status")
def status():
    subprocess.run(["systemctl", "--user", "status", UNIT_NAME])

@smtp_app.command("logs")
def logs():
    subprocess.run(["journalctl", "--user-unit", UNIT_NAME, "-f"])

