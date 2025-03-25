from evrmore_rpc import EvrmoreClient

def get_privkey(address: str):
    """ Get the private key for an address """
    client = EvrmoreClient()
    privkey = client.dumpprivkey(address)
    return privkey