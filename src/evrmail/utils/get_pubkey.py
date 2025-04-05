from evrmore_rpc import EvrmoreClient
import typer

def get_pubkey(address: str):
    """ Use the address to get the public key """
    client = EvrmoreClient()
    address_info = client.validateaddress(address)
    try:
        print(address_info)
        return address_info['pubkey']
    except KeyError:
        print(f"Unable to find public key for address `{address}`")
        raise Exception(f"Unable to find public key for address `{address}`")
    except Exception as e:
        print(f"Failed to get pubkey: {e}")
        raise typer.Exit(code=1)