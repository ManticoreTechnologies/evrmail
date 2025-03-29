import typer
import asyncio
import websockets
import json
from evrmore_rpc import EvrmoreClient
import typer
import asyncio
import websockets
import json
import time
from email import message_from_string
from email.header import decode_header
from pathlib import Path
from evrmore_rpc import EvrmoreClient
from evrmail.daemon import load_inbox, save_inbox, STORAGE_DIR
import json
from email import message_from_string
from email.header import decode_header
from pathlib import Path
import time
STORAGE_DIR = Path.home() / ".evrmail"
INBOX_FILE = STORAGE_DIR / "inbox.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
forward_app = typer.Typer()
WS_SERVER = "ws://mail.evrmail.com:8888/ws"

@forward_app.command("address")
def forward_address(address: str):
    """Connect to EvrMail WebSocket and receive live forwarded mail."""
    asyncio.run(connect_and_listen(address))


async def connect_and_listen(address: str):
    address = address.strip()
    client = EvrmoreClient()
    message = f"evrmail.com: WebSocket login for {address}"

    try:
        signature = await client.signmessage(address, message)
    except Exception as e:
        typer.secho("❌ Failed to sign authentication message.", fg="red")
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    payload = {
        "address": address,
        "message": message,
        "signature": signature
    }

    typer.secho(f"🔌 Connecting to EvrMail WebSocket as {address}...", fg="cyan")

    try:
        async with websockets.connect(WS_SERVER) as ws:
            await ws.send(json.dumps(payload))
            response = await ws.recv()

            # 🛠 FIX: Handle both JSON and raw .eml responses
            try:
                data = json.loads(response)
                if data.get("status") != "ok":
                    typer.secho(f"❌ Auth failed: {data.get('reason', 'Unknown error')}", fg="red")
                    return
                typer.secho("✅ Authenticated. Waiting for forwarded mail...", fg="green")
            except json.JSONDecodeError:
                typer.secho("✅ Authenticated (legacy server response).", fg="green")
                typer.secho("📨 First mail received immediately after auth:", fg="yellow", bold=True)
                typer.echo(response)

            # ✅ Add import at the top if needed
            # from your_file_name import save_mail  # if it's in another module

            # 🔁 Main loop to receive forwarded emails
            while True:
                mail = await ws.recv()
                typer.secho("\n📨 New Mail:", fg="yellow", bold=True)
                save_mail_to_inbox(address, mail)

    except websockets.exceptions.ConnectionClosedError as e:
        typer.secho("❌ WebSocket closed unexpectedly.", fg="red")
        typer.echo(f"Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        typer.secho("❌ Failed to connect or listen.", fg="red")
        typer.echo(str(e))

def save_mail_to_inbox(address: str, mail_content: str):
    """Save parsed metadata from raw email content into the inbox."""
    inbox = load_inbox()
    timestamp = int(time.time())
    msg = message_from_string(mail_content)

    subject, _ = decode_header(msg.get("Subject", "No subject"))[0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors="ignore")
    sender = msg.get("From", "Unknown")
    msg_id = msg.get("Message-ID", f"<{timestamp}@evrmail>")

    mailbox_dir = STORAGE_DIR / "mail" / address
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    eml_path = mailbox_dir / f"msg-{timestamp}.eml"
    eml_path.write_text(mail_content, encoding="utf-8", errors="ignore")

    inbox.append({
        "address": address,
        "from": sender,
        "subject": subject,
        "timestamp": timestamp,
        "message_id": msg_id,
        "path": str(eml_path)
    })
    save_inbox(inbox)
    typer.secho(f"💾 Saved to inbox: {eml_path}", fg="blue")

def save_mail(address: str, mail_content: str):
    """Save the mail as a .eml file and append metadata to inbox.json."""
    mailbox_dir = STORAGE_DIR / "mail" / address
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    filename = mailbox_dir / f"msg-{timestamp}.eml"

    try:
        # Save raw email
        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(mail_content)

        # Parse email metadata
        msg = message_from_string(mail_content)
        subject, _ = decode_header(msg.get("Subject", "No subject"))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors="ignore")
        sender = msg.get("From", "Unknown")
        msg_id = msg.get("Message-ID", f"<{timestamp}@evrmail>")

        # Append summary to inbox
        inbox = load_inbox()
        inbox.append({
            "address": address,
            "from": sender,
            "subject": subject,
            "timestamp": timestamp,
            "message_id": msg_id,
            "path": str(filename)
        })

        with open(INBOX_FILE, "w") as f:
            json.dump(inbox, f, indent=2)

        typer.secho(f"💾 Saved to {filename} and added to inbox.json", fg="blue")

    except Exception as e:
        typer.secho("❌ Failed to save email or update inbox.", fg="red")
        typer.echo(f"Error: {e}")
