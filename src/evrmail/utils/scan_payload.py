import json
from typing import List, Dict, Any
from evrmail.config import load_config
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.ipfs import fetch_ipfs_json
from rich import print

def scan_payload(cid: str) -> List[Dict[str, Any]]:
    """
    Scan a batch payload by IPFS CID and return a list of decrypted messages for known addresses.

    Args:
        cid (str): IPFS CID of the batch payload.

    Returns:
        List[Dict]: Decrypted message dictionaries with 'to', 'from', 'content', and 'raw'.
    """
    batch = fetch_ipfs_json(cid)
    if not batch:
        print(f"[red]❌ Could not fetch or decode payload for CID: {cid}[/red]")
        return []

    config = load_config()
    addresses = config.get("addresses", {})
    messages = batch.get("messages", [])
    batch_id = batch.get("batch_id", "unknown")  # ← get this once
    found_messages = []

    for msg in messages:
        to_address = msg.get("to")
        if to_address in addresses:
            privkey = addresses[to_address].get("privkey")
            if not privkey:
                print(f"[yellow]⚠ No private key configured for address: {to_address}[/yellow]")
                continue

            try:
                decrypted = decrypt_message(msg, privkey)

                # Inject batch_id into raw for saving
                msg["batch_id"] = batch_id

                found_messages.append({
                    "to": to_address,
                    "from": msg.get("from"),
                    "content": decrypted,
                    "raw": msg,
                })
            except Exception as e:
                print(f"[red]❌ Decryption failed for message to {to_address}: {e}[/red]")

    if not found_messages:
        print(f"[blue]ℹ No messages matched your addresses in batch {cid}.[/blue]")
    else:
        print(f"[green]✓ Decrypted {len(found_messages)} message(s) from batch {cid}.[/green]")

    return found_messages
