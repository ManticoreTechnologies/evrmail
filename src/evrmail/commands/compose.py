from evrmail.utils.sign_message import sign_message
from evrmail.config import load_config
from datetime import datetime
from rich.panel import Panel
from evrmail.cli import app
from pathlib import Path
from evrmail.utils.encrypt_message import encrypt_message_with_pubkey
from evrmail.utils.decrypt_message import decrypt_message
from evrmail.utils.get_channel_pubkey import get_channel_pubkey
from evrmail.utils.get_privkey import get_privkey
from evrmail.utils.ipfs import add_to_ipfs
from rich import print
import typer
import json
from evrmail.utils.get_address import get_address
from rich.prompt import Prompt
from evrmail.config import load_config
config = load_config()

def interactive_prompt(label: str, default: str = ""):
    return Prompt.ask(f"[bold cyan]{label}[/]", default=default).strip()


def prompt_for_channel(label: str):
    to_channel = interactive_prompt(f"[bold cyan]{label}[/]", default=config['outbox'])
    try:
        get_address(to_channel)
    except Exception as e:
        print(f"[red]⚠ Channel `{to_channel}` does not exist. Channel must be a valid Evrmore asset. [/red]")
        prompt_for_channel(label)

    return to_channel

@app.command()
def compose():
    """Interactive minimal email composer for evrmail."""
    config = load_config()
    from_channel = config.get("outbox")

    print(Panel.fit("📨 [bold]evrmail Composer[/bold]\nType your message below, or press Ctrl+C to cancel", border_style="green"))

    to_channel = prompt_for_channel("To")
    from_channel = interactive_prompt("From", default=from_channel)
    subject = interactive_prompt("Subject")
    print("\n[dim]Opening editor for body (save + close to finish)[/dim]")
    body = typer.edit("# Delete this and type your message here")

    if not body or body.strip() == "":
        print("[red]❌ Empty message body. Aborting.[/red]")
        raise typer.Exit()

    timestamp = datetime.utcnow().isoformat() + "Z"

    message = {
        "to": to_channel,
        "from": from_channel,
        "subject": subject,
        "timestamp": timestamp,
        "content": body.strip(),
    }

    signature = sign_message(json.dumps(message, sort_keys=True))
    message["signature"] = signature

    print("\n[bold green]✓ Message Ready[/bold green]")
    print(Panel.fit(f"[bold]From:[/bold] {from_channel}\n[bold]To:[/bold] {to_channel}\n[bold]Subject:[/bold] {subject}", border_style="cyan"))

    action = interactive_prompt("\n[bold yellow][S]end or [D]raft?[/bold yellow]", default="D").strip().lower()

    if action == "d":
        drafts_path = Path("drafts")
        drafts_path.mkdir(exist_ok=True)
        # Filename: from_channel_name "to" to_channel_name_timestamp.json
        filename = drafts_path / f"{from_channel.replace('~','_')}_to_{to_channel.replace('~','_')}_{int(datetime.utcnow().timestamp())}.json"
        with open(filename, "w") as f:
            json.dump(message, f, indent=2)
        print(f"[green]📥 Draft saved to[/green] [bold]{filename}[/bold]")
    elif action == "s":
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

        print(f"[bold blue]🚀 Sent! [/bold blue][bold green]Transaction ID: {txid}[/bold green]")
    else:
        print("[red]❌ Invalid action. Message discarded.[/red]")
