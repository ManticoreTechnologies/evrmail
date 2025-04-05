import typer
import requests
import json
from evrmail.config import load_config
from evrmore_rpc import EvrmoreClient

buy_subasset_app = typer.Typer()
EVRMAIL_SERVER = "http://mail.evrmail.com:8888"

@buy_subasset_app.command("buy")
def buy_subasset(alias: str, address_or_friendly_name: str):
    """
    Buy a subasset under the 'EVRMAIL~OUTBOX' asset. This will issue a subasset for the user based on the alias provided.
    """
    # Load the config
    config = load_config()
    addresses = config.get("addresses", {})
    
    # Get the friendly name or address
    target_address = None
    for address, details in addresses.items():
        if details.get("friendly_name", "") == alias or address == address_or_friendly_name:
            target_address = address
            break

    if not target_address:
        typer.echo("❌ No matching address or alias found.")
        raise typer.Exit(1)

    # Get the active address from the config
    from_address = config.get("active_address")
    if not from_address:
        typer.echo("❌ No active address set. Use `evrmail addresses use` to set one.")
        raise typer.Exit(1)

    # Prepare the payload to send to the server
    payload = {
        "username": alias,
        "payment_address": target_address,
        "amount": 5.0,  # You can set the amount as required, e.g., 5 EVR
        "signature": ""  # Assuming you can implement signature handling
    }

    # Send the request to the EvrMail server to purchase the subasset
    try:
        response = requests.post(f"{EVRMAIL_SERVER}/buy_subasset", json=payload)
        if response.status_code == 200:
            typer.echo(f"✅ Subasset purchased successfully. Transaction ID: {response.json()['txid']}")
        else:
            typer.echo(f"❌ Failed to buy subasset: {response.json().get('error', 'Unknown error')}")
    except requests.RequestException as e:
        typer.echo(f"❌ Network error: {e}")
        raise typer.Exit(1)

