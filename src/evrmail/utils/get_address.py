from evrmore_rpc import EvrmoreClient
    
def get_address(channel: str):
    """ Get the address that owns a channel """
    client = EvrmoreClient()
    addresses = client.listaddressesbyasset(channel)
    try:
        return list(addresses.keys())[0]
    except Exception as e:
        raise Exception(f"Channel `{channel}` does not exist")