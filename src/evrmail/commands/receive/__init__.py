import typer
import random
from evrmail.wallet import store

receive_app = typer.Typer()
__all__ = ["receive_app"]

@receive_app.command(name="receive", help="📥 Receive messages")
def receive(
    friendly_name: str = typer.Argument(None, help="🏷️  Friendly name of the sender"),
    wallet_name: str = typer.Option(None, "--wallet", help="👛 Wallet to receive from (random if not specified)"),
):
    """📥 Selects a receive address from a wallet (random if not specified)."""
    from evrmail.wallet.addresses import get_new_address

    # 🎯 Pick a wallet if not provided
    if not wallet_name:
        wallets = store.list_wallets()
        if not wallets:
            typer.echo("❌ No wallets found. Create one with `evrmail wallet create`.")
            raise typer.Exit(1)

        wallet_name = random.choice(wallets)
        typer.echo(f"🎲 No wallet specified — randomly selected: {wallet_name}")

    # 📨 Get the new address
    try:
        if friendly_name:
            address = get_new_address(wallet_name, friendly_name)
        else:
            address = get_new_address(wallet_name)
    except ValueError as e:
        typer.echo(f"❌ {e}")
        raise typer.Exit(1)

    typer.echo(f"📬 Receive address `{address['friendly_name']}`: {address['address']}")
    return address