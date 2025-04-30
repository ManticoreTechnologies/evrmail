import typer
from pathlib import Path
import json
from evrmail.utils.encrypt_message import encrypt_message
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.get_channel_pubkey import get_channel_pubkey
from evrmail.utils.get_privkey import get_privkey
from evrmail.config import load_config
from evrmail.utils.ipfs import add_to_ipfs
config = load_config()
drafts_app = typer.Typer()

@drafts_app.command("list")
def list():
    """List all drafts."""
    drafts_path = Path("drafts")
    if not drafts_path.exists():
        print("No drafts found.")
        return
    for file in drafts_path.glob("*.json"):
        print(file.name.replace(".json", ""))

@drafts_app.command("send")
def send(draft: str):
    """Send a draft."""
    drafts_path = Path("drafts")
    if not drafts_path.exists():
        print("No drafts found.")
        return
    for file in drafts_path.glob("*.json"):
        if draft in file.name:
            with open(file, "r") as f:
                message = json.load(f)
                """ Send the message flow here """
                # Encrypt the message
                pubkey = get_channel_pubkey(message['to'])
                encrypted = encrypt_message_with_pubkey(message, pubkey)
                #privkey = config['outbox_privkey']
                #decrypted = decrypt_message(encrypted, privkey)
                #print(decrypted)
                # Add the message to ipfs
                cid = add_to_ipfs(encrypted)
                # send the message on the blockchain
                from evrmore_rpc import EvrmoreClient
                client = EvrmoreClient()
                txid = client.sendmessage(config['outbox'], cid)[0]
                print(f"Message sent to {message['to']} with CID {cid}")
                print(f"Transaction ID: {txid}")

                # delete the draft
                file.unlink()
                print(f"Draft deleted: {file.name}")
                found = True
                break
    if not found:
        print(f"Draft not found: {draft}")

@drafts_app.command("delete")
def delete(draft: str):
    """Delete a draft."""
    drafts_path = Path("drafts")
    if not drafts_path.exists():
        print("No drafts found.")
        return
    for file in drafts_path.glob("*.json"):
        if draft in file.name:
            file.unlink()