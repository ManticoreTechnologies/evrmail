def sign_message(message: str):
    """Sign a message."""
    from evrmail.config import load_config
    config = load_config()
    address = config['outbox_address']
    from evrmore_rpc import EvrmoreClient
    client = EvrmoreClient()
    signature = client.signmessage(address, message)
    return signature