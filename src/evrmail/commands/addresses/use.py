import typer
from typer import Option
from evrmail import wallet

use_app = typer.Typer()

__all__ = ["use_app"]

@use_app.command(name="use", help="✍️ Set the active address")
def use(address: str=Option(..., "--address", help="The address to use")):
    """Use an address"""
    wallet.set_active_address(address)
    print(f"Active address set to {address}")
