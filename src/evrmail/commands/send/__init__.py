from evrmail.utils.create_batch_payload import create_batch_payload
from evrmore_rpc import EvrmoreClient
from evrmail.commands.ipfs import add_to_ipfs
import typer
from pathlib import Path
from typing import Optional
from evrmail.wallet.tx.create.send_evr import create_send_evr_transaction
from evrmail.wallet import rpc_client
send_app = typer.Typer()

__all__ = ["send_app"]


"""
Reimplement to be like this:
evrmail send evr --to <recipient> --amount <amount> 
evrmail send asset --to <recipient> --asset <asset> --amount <amount>
evrmail send msg --to <recipient> --subject <subject> --body <body>
"""
@send_app.command(name="send", help="🚀 Send EVR from your wallet")
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
    # 🧠 Placeholder logic for implementation — to be replaced with actual send logic
    if not body and not body_file:
        typer.echo("Error: You must provide either --body or --body-file.")
        raise typer.Exit(code=1)

    final_body = body
    if body_file:
        final_body = body_file.read_text()

    is_clearnet = "@" in to
    if is_clearnet:
        typer.echo(f"(dry-run) Sending to clearnet email: {to}")
    else:
        typer.echo(f"(dry-run) Sending to blockchain address/contact: {to}")
        send_blockchain(to, from_address, outbox, subject, final_body, True)


def send_blockchain(to_address: str, from_address: str, outbox: str, subject: str, content: str, dry_run: bool=False):
     # Create the encrypted message payload
    from evrmail.utils.create_message_payload import create_message_payload

    message_payload = create_message_payload(
        to_address,      # To address
        subject,         # Subject
        content          # Body content
    )



    tx, txid = create_send_evr_transaction(from_address, to_address, 1000)
    response = rpc_client.testmempoolaccept([tx])
    if response[0]['txid'] == txid and response[0]['allowed']:
        print("(dry-run) Transaction accepted by evrmore node using testmempool")
    else:
        print("(dry-run) Transaction rejected by evrmore node using testmempool reason:", response[0]['reject-reason'])
        return None
    print("(dry-run) Raw transaction:", tx)
    return txid
