# ─────────────────────────────────────────────────────────
# 📬 evrmail.send.msg
#
# 📜 USAGE:
#   $ evrmail send msg --to <recipient> --outbox <ASSET> --file <path>
#
# 🛠️ DESCRIPTION:
#   Sends a message by transferring a tagged asset with an IPFS CID.
#   Uses the asset name in --outbox to determine the sender address.
#
# 🔧 OPTIONS:
#   --to         Recipient Evrmore address
#   --outbox     Owned asset name (e.g. EVRMAIL~PHOENIX) to send from
#   --file       Path to the message file to upload to IPFS
#   --fee-rate   Fee rate in EVR per kB (default: 0.01)
#   --dry-run    Simulate transaction without broadcasting
#   --debug      Show debug info
#   --raw        Output raw JSON (dry-run only)
# ─────────────────────────────────────────────────────────

import math
import json
import typer
from typing import Optional
from evrmail.wallet import addresses, rpc_client
from evrmail.commands.ipfs import ipfs_add
from evrmail.wallet.addresses import get_outbox_address
from evrmail.wallet.tx.create.send_asset import create_send_asset_transaction

send_msg_app = typer.Typer()
__all__ = ["send_msg_app"]

@send_msg_app.command(name="msg", help="📬 Send an IPFS-backed message")
def send_msg(
    to: str = typer.Option(..., "--to", help="📥 Recipient Evrmore address"),
    outbox: str = typer.Option(..., "--outbox", help="📦 Asset name of your outbox (e.g. EVRMAIL~PHOENIX)"),
    subject: str = typer.Option(..., "--subject", help="📝 Subject of the message"),
    content: str = typer.Option(..., "--content", help="📝 Content of the message"),
    fee_rate: float = typer.Option(0.01, "--fee-rate", help="💸 Fee rate in EVR per kB"),
    dry_run: bool = typer.Option(False, "--dry-run", help="🧪 Simulate transaction without sending"),
    debug: bool = typer.Option(False, "--debug", help="🔍 Show debug info"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON (dry-run only)")
):
    if fee_rate:
        fee_rate = math.ceil(int(fee_rate * 1e8))  # EVR → satoshis

    # 📦 Step 1: Get sender address from asset ownership
    owner_addr = get_outbox_address(outbox)
    if not owner_addr:
        typer.echo(f"❌ You do not appear to own the asset '{outbox}'")
        raise typer.Exit(code=1)

    # Create message payload
    from evrmail.utils.create_message_payload import create_message_payload
    message_payload = create_message_payload(
        to,
        subject,
        content
    )
    print(message_payload)
    return
    # 📤 Step 2: Upload message to IPFS
    cid = ipfs_add(message_payload)
    if not cid:
        typer.echo("❌ Failed to upload message to IPFS")
        raise typer.Exit(code=1)

    # 🔢 Amount = 1 satoshi unit of asset
    asset_qty = 1

    # 🧠 Step 3: Build transaction with IPFS payload
    tx, txid = create_send_asset_transaction(
        from_addresses=[owner_addr],
        to_address=to,
        asset_name=outbox,
        asset_amount=asset_qty,
        fee_rate=fee_rate,
        ipfs_cidv0=cid
    )

    result = rpc_client.testmempoolaccept([tx])
    status = result[0] if result else {}

    if dry_run:
        if raw:
            typer.echo(json.dumps({
                "txid": txid,
                "raw_tx": tx,
                "ipfs": cid,
                "mempool_accept": status
            }, indent=2))
        else:
            if status.get("txid") == txid and status.get("allowed"):
                typer.echo("✅ Transaction accepted by testmempoolaccept ✅")
            else:
                typer.echo(f"❌ Rejected by node: {status.get('reject-reason', 'unknown reason')}")
                return None

        if debug:
            typer.echo("\n🔍 Debug Info:")
            typer.echo("─────────────────────────────────────")
            typer.echo(f"🆔 TXID       : {txid}")
            typer.echo(f"📦 IPFS CID  : {cid}")
            typer.echo(f"🧾 Raw Hex    : {tx}")
            typer.echo("─────────────────────────────────────")

        return txid

    # 📡 Real broadcast
    typer.echo("📡 Broadcasting asset message transaction...")
    tx_hash = rpc_client.sendrawtransaction(tx)
    typer.echo(f"✅ Message sent! TXID: {tx_hash}")
    return tx_hash
