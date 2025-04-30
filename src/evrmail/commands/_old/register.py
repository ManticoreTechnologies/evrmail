import typer
import requests
from evrmore_rpc import EvrmoreClient
from requests.exceptions import RequestException, ConnectionError, Timeout

register_app = typer.Typer()
EVRMAIL_SERVER = "http://mail.evrmail.com:8888"

@register_app.command("address")
def register_address(address: str):
    """Register a new email address with the EvrMail server."""
    address = address.strip()
    message = f"evrmail.com: Register address {address}"

    # Step 1: Sign the message
    try:
        client = EvrmoreClient()
        signature = client.signmessage(address, message)
    except Exception as e:
        typer.secho("❌ Failed to sign message!", fg="red", bold=True)
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)

    payload = {
        "address": address,
        "message": message,
        "signature": signature
    }

    # Step 2: Send the registration request
    try:
        response = requests.post(f"{EVRMAIL_SERVER}/register_email", json=payload, timeout=5)

        if response.status_code == 200:
            typer.secho(f"{response.json().get('message')}", fg="green", bold=True)

        elif response.status_code == 409:
            typer.secho("⚠️ Address already registered.", fg="yellow")
            typer.echo(f"Address: {address}")
        elif response.status_code == 400:
            typer.secho("❌ Invalid address or signature.", fg="red")
            typer.echo(f"Server response: {response.json().get('error')}")
        else:
            typer.secho("❌ Server rejected the request.", fg="red")
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Details: {response.text}")

    except ConnectionError:
        typer.secho("🚫 Could not connect to the EvrMail server!", fg="red", bold=True)
    except Timeout:
        typer.secho("⏱️ Connection to EvrMail server timed out.", fg="red")
    except RequestException as e:
        typer.secho("❌ Unexpected network error occurred.", fg="red")
        typer.echo(str(e))

@register_app.command("webhook")
def register_webhook(address: str, url: str):
    """Register a webhook to receive mail for a specific Evrmore address."""
    address = address.strip()
    url = url.strip()
    message = f"evrmail.com: Register webhook {url} for {address}"

    # Step 1: Sign the message
    try:
        client = EvrmoreClient()
        signature = client.signmessage(address, message)
    except Exception as e:
        typer.secho("❌ Failed to sign webhook registration message!", fg="red", bold=True)
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)

    payload = {
        "address": address,
        "webhook_url": url,
        "message": message,
        "signature": signature
    }

    # Step 2: Send the webhook registration
    try:
        response = requests.post(f"{EVRMAIL_SERVER}/register_webhook", json=payload, timeout=5)

        if response.status_code == 200:
            typer.secho(f"✅ Webhook registered for {address}", fg="green", bold=True)
            typer.echo(f"📡 Webhook URL: {url}")

        elif response.status_code == 409:
            typer.secho("⚠️ Webhook already registered for this address.", fg="yellow")
            typer.echo(f"Address: {address}")
        elif response.status_code == 400:
            typer.secho("❌ Invalid request or signature.", fg="red")
            typer.echo(f"Server response: {response.json().get('error')}")
        else:
            typer.secho("❌ Server rejected the webhook request.", fg="red")
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Details: {response.text}")

    except ConnectionError:
        typer.secho("🚫 Could not connect to the EvrMail server!", fg="red", bold=True)
    except Timeout:
        typer.secho("⏱️ Connection to EvrMail server timed out.", fg="red")
    except RequestException as e:
        typer.secho("❌ Unexpected network error occurred.", fg="red")
        typer.echo(str(e))
