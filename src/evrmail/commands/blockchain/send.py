""" Send a message through the evrmore blockchain! 

    Encrypts the message, adds it to a batch payload, and sends it!

    This method only sends a single message, other batch methods will be added later.
"""

from evrmail.utils.get_pubkey import get_pubkey
from evrmail.utils.sign_message import sign_message
from evrmail.utils.encrypt_message import encrypt_message
from evrmail.utils.ipfs import add_to_ipfs
from evrmail.config import load_config
from datetime import datetime
from evrmore_rpc import EvrmoreClient
import json
import typer

send_app = typer.Typer()

@send_app.command("send")
def send_message(to_address: str, subject: str, content: str) -> str:
    """
    🏹 Send a single encrypted EvrMail message to the specified address.

    Args:
        to_address (str): The recipient's address (e.g. ELzeXRHkse15xm7Ra8o6YtYjZoCjkvhXqB).
        subject (str): Subject of the message.
        content (str): The message body (plaintext).

    Returns:
        str: Transaction ID of the blockchain message.
    """

    # First make sure we have all proper configs set
    from evrmail.config import load_config
    config = load_config()
    try:
        if len(config.get('addresses')) == 0:
            print("You must save at least one address to send an evrmail: evrmail addresses add <address> --friendly-name <friendly_name> ")
            return
        if config.get('active_address') is None:
            print("You must select a saved address to send from: evrmail addresses use <address or friendly_name>.")
            return
        if config.get('outbox') is None:
            print("You must specify an outbox asset to broadcast messages: evrmail blockchain outbox set <owned_asset_name>")
            return
    except:
        return
    # Now create the encrypted message payload
    from evrmail.utils.create_message_payload import create_message_payload
    message_payload = create_message_payload(
        "EL3BmmjmDa5LNMmF8fE4smdfxLmi8EJJMR", # To address
        "Subject here",                       # Subject
        "content"                             # Body content
    )
    
    # Add the payload to a batch
    from evrmail.utils.create_batch_payload import create_batch_payload
    my_batch = create_batch_payload(
        [message_payload]
    )

    # Add to IPFS
    cid = add_to_ipfs(my_batch)

    print ("Uploaded to ipfs ",cid)

    # Broadcast the message to the evrmore blockchain
    from evrmore_rpc import EvrmoreClient
    rpc = EvrmoreClient()
    txid = rpc.sendmessage(config["outbox"], cid)
    print(f"Blockchain message transaction successfully sent: {txid[0]}")
    return txid[0]
