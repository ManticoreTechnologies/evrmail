import typer
import requests
from email.message import EmailMessage
from evrmail.config import load_config
from evrmore_rpc import EvrmoreClient

send_app = typer.Typer()
EVRMAIL_SERVER = "http://mail.evrmail.com:8888"

@send_app.command("send")
def send(email: str, subject: str, body: str):
    """
    Send an email to a clearnet address via EvrMail forwarding.
    """
    config = load_config()
    from_address = config.get("active_address")

    if not from_address:
        typer.echo("❌ No active address set. Use `evrmail addresses use` to set one.")
        raise typer.Exit(1)

    # ✉️ Construct the expected message format for signature
    message_to_sign = f"evrmail.com: Send mail from {from_address} to {email} subject {subject}"

    # 🔐 Sign the message using the wallet (or external signer)
    rpc = EvrmoreClient()
    print(from_address)
    try:
        signature = rpc.signmessage(from_address, message_to_sign)
    except Exception as e:
        typer.echo(f"❌ Failed to sign message: {e}")
        raise typer.Exit(1)

    # 📬 Build the request payload
    payload = {
        "from_address": from_address,
        "to": email,
        "subject": subject,
        "body": body,
        "signature": signature
    }

    # 🌐 Send the request to the EvrMail relay
    try:
        response = requests.post(f"{EVRMAIL_SERVER}/send_email", json=payload)
        if response.status_code == 200:
            typer.echo("✅ Email sent successfully.")
        else:
            typer.echo(f"❌ Failed to send email: {response.json().get('error', 'Unknown error')}")
    except requests.RequestException as e:
        typer.echo(f"❌ Network error: {e}")
        raise typer.Exit(1)
