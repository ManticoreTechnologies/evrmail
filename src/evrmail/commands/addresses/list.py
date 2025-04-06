from evrmail import wallet
import typer
from typer import Option
list_app = typer.Typer()

# wallet name is optional
@list_app.command(name="list", help="📬 List all addresses from all wallets")
def list(wallet_name: str=Option(None, "--wallet", help="📬 List addresses in one wallet")):
    """List all addresses in the wallet."""
    if not wallet_name:
        # list all addresses 
        addresses = wallet.addresses.get_all_addresses()
    else:
        loaded_wallet = wallet.load_wallet(wallet_name)
        addresses = loaded_wallet.get_addresses()
    for address in addresses:
        print(address)