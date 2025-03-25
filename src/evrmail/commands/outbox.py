from evrmail.config import load_config, save_config
from evrmail.utils.get_privkey import get_privkey
from evrmail.utils.get_pubkey import get_pubkey
from evrmore_rpc import EvrmoreClient
import typer

outbox_app = typer.Typer()

""" evrmail outbox set <outbox> """
@outbox_app.command("set")
def set_outbox(outbox: str):
    
    """Set the outbox to use."""

    # Check if the outbox exists
    client = EvrmoreClient()
    addresses = client.listaddressesbyasset(outbox)
    if type(addresses) is not dict:
        print(f"Outbox `{outbox}` does not exist")
        raise typer.Exit(code=1)

    # Set the outbox in the config
    config = load_config()
    config['outbox'] = outbox

    # Get the address that owns the outbox
    try:
        address = list(addresses.keys())[0]
    except:
        print(f"Outbox `{outbox}` does not exist")
        raise typer.Exit(code=1)

    # Set the address, pubkey, and privkey in the config
    from evrmail.utils.wif_to_privkey_hex import wif_to_privkey_hex
    config['outbox_address'] = address
    config['outbox_pubkey'] = get_pubkey(address)
    config['outbox_privkey'] = wif_to_privkey_hex(get_privkey(address))

    # Save the config
    save_config(config)

    # Print the result
    print(f"Set outbox to `{outbox}`")

""" evrmail outbox get """
@outbox_app.command("get")
def get_outbox():
    """Get the outbox."""
    config = load_config()
    print(f"Outbox: {config['outbox']}")
    print(f"Address: {config['outbox_address']}")
    print(f"Pubkey: {config['outbox_pubkey']}")
    print(f"Privkey: {config['outbox_privkey']}")



