import typer
from typer import Option
from evrmail import wallet

publickey_app = typer.Typer()

__all__ = ["publickey_app"]

@publickey_app.command(name="publickey", help="🔍 Get public key for an address (if known)")
def publickey(address: str=Option(..., "--address", help="The address to get the public key for")):
    """Get the public key for an address"""
    print(f"Public key for address {address}: {wallet.get_public_key(address)}")
