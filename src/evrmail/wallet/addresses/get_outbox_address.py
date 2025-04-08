from .get_all_addresses import get_all_addresses
from evrmail.wallet import rpc_client

def get_outbox_address(outbox: str) -> str:
    address_balances = rpc_client.listaddressesbyasset(outbox)
    my_addresses = get_all_addresses()
    for address in my_addresses:
        if address in address_balances:
            return address
    return None