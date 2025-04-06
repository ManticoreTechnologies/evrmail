import typer
from typer import Option
from evrmail import wallet

validate_app = typer.Typer()

__all__ = ["validate_app"]

@validate_app.command(name="validate", help="✅ Validate any Evrmore address")
def validate(address: str=Option(..., "--address", help="The address to validate")):
    """Validate an address"""
    wallet.addresses.validate(address)
    print(f"Address {address} is valid")
