import typer
from typer import Option
from evrmail import wallet

dumpprivkey_app = typer.Typer()

__all__ = ["dumpprivkey_app"]

@dumpprivkey_app.command(name="dumpprivkey", help="🔓 Dump WIF private key for an address")
def dumpprivkey(address: str=Option(..., "--address", help="The address to dump the private key for")):
    """Dump the private key for an address"""
    print(f"Private key for address {address}: {wallet.dump_private_key(address)}")
