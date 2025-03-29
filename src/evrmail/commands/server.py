import typer
import subprocess
import signal
import os
from pathlib import Path

server_app = typer.Typer()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT
SERVER_SCRIPT = SRC_DIR / "evrmail" / "server" / "mailserver.py"
PID_FILE = PROJECT_ROOT / "mailserver.pid"
LOG_FILE = PROJECT_ROOT / "mailserver.log"
CONFIG_FILE = Path.home() / ".evrmail" / "server_config.json"

@server_app.command("start")
def start():
    """Start the EvrMail mail server."""
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, 0)
            typer.echo(f"⚠️  Mail server is already running (PID: {pid})")
            raise typer.Exit()
        except ProcessLookupError:
            typer.echo("🧹 Found stale PID file. Cleaning up...")
            PID_FILE.unlink()

    if not SERVER_SCRIPT.exists():
        typer.echo(f"❌ Server script not found: {SERVER_SCRIPT}")
        raise typer.Exit(1)

    log = open(LOG_FILE, "a")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    process = subprocess.Popen(
        ["python3", str(SERVER_SCRIPT)],
        cwd=SRC_DIR,
        env=env,
        stdout=log,
        stderr=log,
        start_new_session=True
    )
    PID_FILE.write_text(str(process.pid))
    typer.echo(f"✅ Mail server started (PID: {process.pid})")

@server_app.command("stop")
def stop():
    """Stop the EvrMail mail server."""
    if not PID_FILE.exists():
        typer.echo("ℹ️  Mail server is not running.")
        raise typer.Exit()

    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, signal.SIGTERM)
        typer.echo(f"🛑 Stopped mail server (PID: {pid})")
    except ProcessLookupError:
        typer.echo(f"⚠️  No process with PID {pid}. Removing stale PID file.")
    finally:
        PID_FILE.unlink(missing_ok=True)

@server_app.command("restart")
def restart():
    """Restart the EvrMail mail server."""
    stop()
    start()

@server_app.command("status")
def status():
    """Check the status of the EvrMail mail server."""
    if not PID_FILE.exists():
        typer.echo("ℹ️  Mail server is not currently running.")
        raise typer.Exit()

    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, 0)
        typer.echo(f"✅ Mail server is running (PID: {pid})")
    except ProcessLookupError:
        typer.echo(f"⚠️  No process found with PID {pid}. Cleaning up...")
        PID_FILE.unlink(missing_ok=True)
    except Exception as e:
        typer.echo(f"❌ Error checking mail server status: {e}")
        raise typer.Exit(1)

@server_app.command("logs")
def logs(clear: bool = typer.Option(False, "--clear", help="Clear the log file first")):
    """View logs for the mail server."""
    if not LOG_FILE.exists():
        typer.echo("ℹ️  No logs found.")
        raise typer.Exit()

    if clear:
        LOG_FILE.write_text("")
        typer.echo("🧹 Cleared mail server logs.")
        raise typer.Exit()

    with open(LOG_FILE, "r") as f:
        typer.echo(f.read())

@server_app.command("config")
def config():
    """Show or edit the mail server config (domain, DKIM, ports, etc)."""
    typer.echo("✏️ Edit this file to configure EvrMail server:")
    typer.echo(CONFIG_FILE)
    typer.echo("(You can create it if it doesn't exist.)")