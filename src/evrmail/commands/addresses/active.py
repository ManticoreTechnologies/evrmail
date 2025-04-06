import typer
from typer import Option
active_app = typer.Typer()
from evrmail import wallet

__all__ = ["active_app"]

@active_app.command(name="active", help="⭐ Show currently selected address")
def active():
    """Show the currently selected address"""
    address = wallet.get_active_address()
    print(f"Active address: {address}")
