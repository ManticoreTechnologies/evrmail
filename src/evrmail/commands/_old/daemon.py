import typer
import subprocess
import signal
import os
import json
import time
from pathlib import Path
from evrmail.config import load_config
from evrmail.utils.ipfs import fetch_ipfs_json
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.scan_payload import scan_payload
from evrmail.utils.wif_to_privkey_hex import wif_to_privkey_hex


daemon_app = typer.Typer()

BASE_DIR = Path.home() / ".evrmail"
PID_FILE = BASE_DIR / "daemon.pid"
LOG_FILE = BASE_DIR / "daemon.log"

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
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)

    SRC_DIR = Path(__file__).resolve().parents[2]

    process = subprocess.Popen(
        ["python3", "evrmail/daemon/__main__.py"],
        cwd=SRC_DIR,
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
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
        typer.echo(f"🛌 Sent SIGTERM to daemon (PID: {pid})")
    except ProcessLookupError:
        typer.echo(f"⚠️  No process found with PID {pid} — removing stale PID file.")
    finally:
        PID_FILE.unlink(missing_ok=True)

@daemon_app.command("restart")
def restart():
    """Restart the evrmail daemon."""
    stop()
    start()

@daemon_app.command("status")
def status():
    """Check the status of the evrmail daemon."""
    if not PID_FILE.exists():
        typer.echo("ℹ️  Daemon is not currently running.")
        raise typer.Exit()

    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, 0)
        typer.echo(f"✅ Daemon is running (PID: {pid})")
    except ProcessLookupError:
        typer.echo(f"⚠️  No process found with PID {pid} — removing stale PID file.")
        PID_FILE.unlink(missing_ok=True)
    except Exception as e:
        typer.echo(f"❌ Error checking daemon status: {e}")
        raise typer.Exit(1)

@daemon_app.command("logs")
def logs(clear: bool = typer.Option(False, "--clear", "-c", help="Clear the daemon log after displaying.")):
    """Display the logs of the evrmail daemon."""
    if not LOG_FILE.exists():
        typer.echo("ℹ️  No logs found.")
        raise typer.Exit()

    with open(LOG_FILE, "r") as f:
        typer.echo(f.read())

    if clear:
        LOG_FILE.write_text("")
        typer.echo("🧹 Logs cleared.")

@daemon_app.command("check")
def check(cid: str):
    """Manually check a given IPFS CID for messages to addresses in config."""
    config = load_config()
    known_addresses = config.get("addresses", {})
    payload = fetch_ipfs_json(cid)
    messages = scan_payload(payload)

    found = []

    for msg in messages:
        recipient = msg.get("to")
        if recipient in known_addresses:
            try:
                priv_wif = known_addresses[recipient].get("privkey")
                privkey = wif_to_privkey_hex(priv_wif)
                decrypted = decrypt_message(msg, privkey)
                decrypted["cid"] = cid
                decrypted["received_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                decrypted["read"] = False
                found.append(decrypted)
            except Exception as e:
                typer.echo(f"❌ Failed to decrypt message for {recipient}: {e}")

    if not found:
        typer.echo("❌ No messages found for your addresses in this CID.")
    else:
        typer.echo(f"✅ Found {len(found)} messages for your addresses:")
        for msg in found:
            typer.echo(json.dumps(msg, indent=2))
