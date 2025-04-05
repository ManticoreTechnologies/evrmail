from evrmail.utils.create_batch_payload import create_batch_payload
from evrmore_rpc import EvrmoreClient
import typer
from pathlib import Path
from typing import Optional

send_app = typer.Typer()

__all__ = ["send_app"]

@send_app.command()
def send(
    from_address: str = typer.Option(..., "--from", help="Your wallet address or label (must be unlocked)"),
    outbox: str = typer.Option(..., "--outbox", help="Owned asset used to send message (e.g. EVRMAIL#PHOENIX)"),
    to: str = typer.Option(..., "--to", help="Recipient's address or saved contact label"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Subject line of the message"),
    body: Optional[str] = typer.Option(None, "--body", help="Message body (plain text)"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", exists=True, file_okay=True, dir_okay=False, readable=True, help="Load message body from a text file"),
    encrypt: bool = typer.Option(False, "--encrypt", help="Encrypt message using recipient's public key"),
    reply_to: Optional[str] = typer.Option(None, "--reply-to", help="Message ID this is replying to"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate the message send without broadcasting"),
    debug: bool = typer.Option(False, "--debug", help="Show raw transaction and debug info")
):
    """
    Send a message via EvrMail using a local wallet and outbox asset.
    """
    # 🧠 Placeholder logic for implementation — to be replaced with actual send logic
    if not body and not body_file:
        typer.echo("Error: You must provide either --body or --body-file.")
        raise typer.Exit(code=1)

    final_body = body
    if body_file:
        final_body = body_file.read_text()

    is_clearnet = "@" in to
    if is_clearnet:
        typer.echo(f"Sending to clearnet email: {to}")
    else:
        typer.echo(f"Sending to blockchain address/contact: {to}")
        send_blockchain(to, from_address, outbox, subject, final_body, True)


def send_blockchain(to_address: str, from_address: str, outbox: str, subject: str, content: str, dry_run: bool=False):
     # Create the encrypted message payload
    from evrmail.utils.create_message_payload import create_message_payload

    message_payload = create_message_payload(
        to_address,      # To address
        subject,         # Subject
        content          # Body content
    )

    # Add the payload to a batch
    
    my_batch = create_batch_payload([
        message_payload
    ])

    # Add to IPFS
    cid = add_to_ipfs(my_batch)
    print("Uploaded to IPFS:", cid)

    if not dry_run:
        # Broadcast the message to the Evrmore blockchain using the active address
        rpc = EvrmoreClient()
        txid = rpc.sendmessage(outbox, cid, sender=from_address)
        print(f"Blockchain message transaction successfully sent: {txid[0]}")
        return txid[0]