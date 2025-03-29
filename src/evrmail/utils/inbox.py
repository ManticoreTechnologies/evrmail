import os
import json
import time
from pathlib import Path
from typing import List, Dict

def save_messages(messages: List[Dict]):
    """
    Save a list of decrypted messages to the inbox.
    Each message is stored in ~/.evrmail/mail/INBOX/<address>/timestamp_batchid.json
    Includes full raw payload for traceability.
    """
    base_dir = Path.home() / ".evrmail" / "mail" / "INBOX"
    base_dir.mkdir(parents=True, exist_ok=True)

    for msg in messages:
        to_address = msg["to"]
        address_dir = base_dir / to_address
        address_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
        batch_id = msg["raw"].get("batch_id", "unknown")
        filename = f"{timestamp}_{batch_id}.json"

        message_data = {
            "to": msg["to"],
            "from": msg["from"],
            "received_at": timestamp,
            "content": msg["content"],
            "raw": msg["raw"]  # fully store raw payload
        }

        filepath = address_dir / filename
        with open(filepath, "w") as f:
            json.dump(message_data, f, indent=2)

        print(f"[green]📥 Saved message to {filepath}[/green]")

def load_all_messages() -> List[Dict]:
    """
    Load all saved messages from ~/.evrmail/mail/INBOX/<address>/*.
    Returns a flat list of message dicts, each with a __path key.
    """
    base_dir = Path.home() / ".evrmail" / "mail" / "INBOX"
    messages = []

    if not base_dir.exists():
        return messages

    for address_dir in base_dir.iterdir():
        if address_dir.is_dir():
            for msg_file in address_dir.glob("*.json"):
                try:
                    with open(msg_file, "r") as f:
                        msg = json.load(f)
                        msg["__path"] = str(msg_file)
                        msg["timestamp"] = msg.get("received_at", "")
                        messages.append(msg)
                except Exception as e:
                    print(f"⚠️ Failed to read message {msg_file}: {e}")

    # Sort by timestamp descending
    messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return messages

def delete_message_by_path(path: str):
    """
    Delete a message file by its full path.
    """
    try:
        os.remove(path)
        print(f"[red]🗑 Deleted message {path}[/red]")
    except Exception as e:
        print(f"❌ Failed to delete message {path}: {e}")
