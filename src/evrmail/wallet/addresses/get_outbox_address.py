from .get_all_addresses import get_all_addresses

def get_outbox_address(outbox: str) -> str:
    from evrmail import rpc_client
    address_balances = rpc_client.listaddressesbyasset(outbox)
    my_addresses = get_all_addresses()
    for address in my_addresses:
        if address in address_balances:
            return address
    return None