import typer
import subprocess
import signal
import os
from pathlib import Path

daemon_app = typer.Typer()
PID_FILE = Path("daemon.pid")
LOG_FILE = Path("daemon.log")

@daemon_app.command("start")
def start():
    """Start the evrmail daemon in the background."""
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, 0)
            typer.echo(f"⚠️  Daemon is already running (PID: {pid})")
            raise typer.Exit()
        except ProcessLookupError:
            typer.echo("🧹 Stale PID file found. Cleaning up...")
            PID_FILE.unlink()

    log = open(LOG_FILE, "a")
    # NOTE: The module path here is evrmail.daemon.__main__
    process = subprocess.Popen(
        ["python3", "-m", "evrmail.daemon"],
        stdout=log,
        stderr=log,
        start_new_session=True
    )
    PID_FILE.write_text(str(process.pid))
    typer.echo(f"✅ Daemon started in background (PID: {process.pid})")

@daemon_app.command("stop")
def stop():
    """Stop the evrmail daemon."""
    if not PID_FILE.exists():
        typer.echo("ℹ️  Daemon is not currently running.")
        raise typer.Exit()

    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, signal.SIGTERM)
        typer.echo(f"🛑 Sent SIGTERM to daemon (PID: {pid})")
    except ProcessLookupError:
        typer.echo(f"⚠️  No process found with PID {pid} — removing stale PID file.")
    finally:
        PID_FILE.unlink(missing_ok=True)
