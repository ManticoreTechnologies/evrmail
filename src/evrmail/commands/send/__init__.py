# ─────────────────────────────────────────────────────────────
# 🚀 evrmail.send
#
# 📜 USAGE:
#   $ evrmail send evr --to <recipient> --amount <amount>
#   $ evrmail send asset --to <recipient> --asset <asset_name> --amount <amount>
#   $ evrmail send msg --to <recipient> --subject <subject> --body <body>
#
# 🛠️ DESCRIPTION:
#   Send EVR, assets, or messages on the Evrmore blockchain or to clearnet email.
#   - EVR:     transfer coins to another address
#   - asset:   send a specific asset
#   - msg:     send encrypted (or plain) metadata messages
#
# 🔧 OPTIONS:
#   --from        Sender address (must be unlocked)
#   --outbox      Asset used to send metadata messages (e.g., EVRMAIL#YOURNAME)
#   --to          Recipient address or email
#   --subject     Message subject (for metadata)
#   --body        Message content (inline)
#   --body-file   Load message body from file
#   --encrypt     Encrypt metadata using recipient's pubkey
#   --reply-to    Set message this is replying to
#   --dry-run     Print tx and simulate without broadcasting
#   --debug       Show debug info (raw tx)
#   --raw         Output raw JSON (dry-run only)
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.utils.create_batch_payload import create_batch_payload
from evrmore_rpc import EvrmoreClient
from evrmail.commands.ipfs import add_to_ipfs
import typer
from pathlib import Path
from typing import Optional
from evrmail.wallet.tx.create.send_evr import create_send_evr_transaction
from evrmail.wallet import rpc_client
import json

# 🚀 Typer App Init
send_app = typer.Typer()
__all__ = ["send_app"]

# ─────────────────────────────────────────────────────────────
# ✉️ Send Command
# ─────────────────────────────────────────────────────────────
@send_app.command(name="send", help="🚀 Send EVR, assets, or metadata messages")
def send(
    from_address: str = typer.Option(..., "--from", help="🧾 Your address (must be unlocked)"),
    outbox: str = typer.Option(..., "--outbox", help="📦 Outbox asset used for metadata (e.g., EVRMAIL#PHOENIX)"),
    to: str = typer.Option(..., "--to", help="🎯 Recipient address or contact/email"),
    subject: Optional[str] = typer.Option(None, "--subject", help="📝 Subject line of the message"),
    body: Optional[str] = typer.Option(None, "--body", help="✏️ Inline message body"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", exists=True, file_okay=True, dir_okay=False, readable=True, help="📁 Load message body from file"),
    encrypt: bool = typer.Option(False, "--encrypt", help="🔐 Encrypt message using recipient pubkey"),
    reply_to: Optional[str] = typer.Option(None, "--reply-to", help="🔁 Message ID this replies to"),
    dry_run: bool = typer.Option(False, "--dry-run", help="🧪 Simulate the send without broadcasting"),
    debug: bool = typer.Option(False, "--debug", help="🐛 Show raw transaction and debug info"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON (dry-run only)")
):
    # 🧠 Validate input body
    if not body and not body_file:
        typer.echo("❌ Error: You must provide either --body or --body-file.")
        raise typer.Exit(code=1)

    final_body = body_file.read_text() if body_file else body
    is_clearnet = "@" in to

    if is_clearnet:
        typer.echo(f"(dry-run) Sending to clearnet email: {to}")
        # Future: Add clearnet SMTP relay
    else:
        typer.echo(f"(dry-run) Sending to blockchain address/contact: {to}")
        result = send_blockchain(
            to_address=to,
            from_address=from_address,
            outbox=outbox,
            subject=subject,
            content=final_body,
            dry_run=dry_run,
            debug=debug,
            raw=raw
        )
        if result and not raw:
            typer.echo(f"✅ Dry-run TXID: {result}")


# ─────────────────────────────────────────────────────────────
# 🔗 Send Metadata via Blockchain
# ─────────────────────────────────────────────────────────────
def send_blockchain(
    to_address: str,
    from_address: str,
    outbox: str,
    subject: str,
    content: str,
    dry_run: bool = False,
    debug: bool = False,
    raw: bool = False
):
    from evrmail.utils.create_message_payload import create_message_payload
    payload = create_message_payload(to_address, subject, content)

    # Future: attach IPFS hash if needed
    tx, txid = create_send_evr_transaction(from_address, to_address, 1000)

    result = rpc_client.testmempoolaccept([tx])
    status = result[0] if result else {}

    if raw:
        typer.echo(json.dumps({
            "txid": txid,
            "raw_tx": tx,
            "mempool_accept": status
        }, indent=2))
        return txid

    if status.get("txid") == txid and status.get("allowed"):
        typer.echo("✅ Transaction accepted by testmempoolaccept ✅")
    else:
        typer.echo(f"❌ Rejected by node: {status.get('reject-reason', 'unknown reason')}")
        return None

    if debug:
        typer.echo("\n🐛 Debug Info:")
        typer.echo(f"TXID: {txid}")
        typer.echo(f"Raw TX: {tx}")

    return txid
