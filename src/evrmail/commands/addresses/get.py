import typer
from typer import Option
from evrmail.wallet import utils
get_app = typer.Typer()

__all__ = ["get_app"]

@get_app.command(name="get", help="🔢 Get address by index")
def get(index: int=Option(None, "--index", help="Index of the address to get"),
        outbox: str=Option(None, "--outbox", help="Outbox address"),
        ):
    """Get an address from the wallet."""
    if outbox:
        address_info = utils.get_address_by_asset(outbox)
        print(address_info)
    else:
        address_info = utils.get_address_info(index)
        print(address_info)

