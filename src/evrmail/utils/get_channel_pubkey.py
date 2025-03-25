from evrmail.utils.get_pubkey import get_pubkey
from evrmail.utils.get_address import get_address
def get_channel_pubkey(channel: str):
    """ Get the pubkey of the address that owns a channel """
    address = get_address(channel)
    return get_pubkey(address)