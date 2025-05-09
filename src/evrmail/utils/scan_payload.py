import json
from typing import List, Dict, Any
from evrmail.config import load_config
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.ipfs import fetch_ipfs_json
from rich import print
from evrmail.wallet.utils import list_wallets, load_wallet
import logging

def get_wallet_decryption_keys() -> Dict[str, str]:
    """Returns a mapping of addresses to their private keys from all wallets."""
    keymap = {}
    for name in list_wallets():
        wallet = load_wallet(name)
        addresses = wallet.get("addresses", [])
        for address in addresses:
            address_data = addresses[address]
            keymap[address] = address_data.get("private_key")
    return keymap

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

    keymap = get_wallet_decryption_keys()
    messages = batch.get("messages", [])
    batch_id = batch.get("batch_id", "unknown")
    found_messages = []
    
    # Check if this is a contact request batch
    if batch_id and isinstance(batch_id, str) and batch_id.startswith("contact_req_"):
        print(f"[cyan]📇 Detected contact request batch: {batch_id}[/cyan]")
        # Extra debug for contact request batch
        print(f"[cyan]Batch payload structure: {json.dumps(batch, indent=2)}[/cyan]")
    
    if type(messages) is list:
        for message in messages:
            msg = message
            try:
                print(f"[DEBUG] Message raw payload:\n{json.dumps(msg, indent=2)}")
                to_address = msg.get("to")
                
                # Check if this is a contact request message
                if msg.get("type") == "contact_request":
                    print(f"[cyan]📇 Found contact request in batch[/cyan]")
                    
                    # Even if not for us, log it for debugging
                    if to_address not in keymap:
                        logging.info(f"Contact request found but not for our addresses: {to_address}")
                        print(f"[yellow]Contact request not for our addresses: {to_address}[/yellow]")
                        continue

                # Check if message is for one of our addresses
                if to_address in keymap:
                    privkey = keymap[to_address]
                    if not privkey:
                        print(f"[yellow]⚠ No private key configured for address: {to_address}[/yellow]")
                        continue
                    
                    # Process based on encrypted flag
                    if msg.get("encrypted", True) == True:    
                        decrypted = decrypt_message(msg, privkey)
                    else:
                        decrypted = msg
                        # For non-encrypted messages, preserve the original message type
                        # This helps with identifying contact requests
                        print(f"[green]Message is not encrypted, preserving original data[/green]")
                    
                    msg["batch_id"] = batch_id
                    found_messages.append({
                        "to": to_address,
                        "from": msg.get("from"),
                        "content": decrypted,
                        "raw": msg,
                    })
            except Exception as e:
                print(f"[red]❌ Decryption failed for message to {msg.get('to', '<unknown>')}: {e}[/red]")
    elif type(messages) is dict:
        msg = messages
        try:
            print(f"[DEBUG] Message raw payload:\n{json.dumps(msg, indent=2)}")
            to_address = msg.get("to")
            
            # Check if this is a contact request message
            if msg.get("type") == "contact_request":
                print(f"[cyan]📇 Found single contact request message[/cyan]")
                
                # Even if not for us, log it for debugging
                if to_address not in keymap:
                    logging.info(f"Contact request found but not for our addresses: {to_address}")
                    print(f"[yellow]Contact request not for our addresses: {to_address}[/yellow]")

            if to_address in keymap:
                privkey = keymap[to_address]
                if not privkey:
                    print(f"[yellow]⚠ No private key configured for address: {to_address}[/yellow]")
                if msg.get("encrypted", True) == True:    
                    decrypted = decrypt_message(msg, privkey)
                else:
                    decrypted = msg
                    # For non-encrypted messages, preserve the original message type
                    print(f"[green]Message is not encrypted, preserving original data[/green]")
                
                msg["batch_id"] = batch_id
                found_messages.append({
                    "to": to_address,
                    "from": msg.get("from"),
                    "content": decrypted,
                    "raw": msg,
                })
        except Exception as e:
            print(f"[red]❌ Decryption failed for message to {msg.get('to', '<unknown>')}: {e}[/red]")


    if not found_messages:
        print(f"[blue]ℹ No messages matched your addresses in batch {cid}.[/blue]")
    else:
        print(f"[green]✓ Decrypted {len(found_messages)} message(s) from batch {cid}.[/green]")

    return found_messages
