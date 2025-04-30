# ─────────────────────────────────────────────────────────
# 🚀 evrmail.send
#
# 📜 USAGE:
#   $ evrmail send evr --to <recipient> --amount <amount>
#
# 🛠️ DESCRIPTION:
#   Send EVR to another address on the Evrmore blockchain.
#
# 🔧 OPTIONS:
#   --from        (optional) Sender address (uses first wallet address if omitted)
#   --to          Recipient address
#   --amount      Amount in EVR to send
#   --dry-run     Print tx and simulate without broadcasting
#   --debug       Show debug info (raw tx)
#   --raw         Output raw JSON (dry-run only)
# ─────────────────────────────────────────────────────────

# 📦 Imports
import math
from evrmore_rpc import EvrmoreClient
import typer
from typing import Optional
from evrmail.wallet.tx.create.send_evr import create_send_evr_transaction
import json

# 🚀 Typer App Init
send_evr_app = typer.Typer()
__all__ = ["send_evr_app"]

# ─────────────────────────────────────
# ✉️ Send Command
# ─────────────────────────────────────
@send_evr_app.command(name="evr", help="🚀 Send EVR")
def send(
    from_address: Optional[str] = typer.Option(None, "--from", help="📿 Optional sender address (must be unlocked)"),
    to: str = typer.Option(..., "--to", help="🌟 Recipient address"),
    amount: float = typer.Option(..., "--amount", help="💰 Amount of EVR to send"),
    fee_rate: float = typer.Option(0.01, "--fee-rate", help="💰 Fee rate in evr per kB"),
    dry_run: bool = typer.Option(False, "--dry-run", help="🧪 Simulate the send without broadcasting"),
    debug: bool = typer.Option(False, "--debug", help="🔋 Show raw transaction and debug info"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON (dry-run only)")
):
    from evrmail import rpc_client
    from evrmail.wallet import addresses
    if fee_rate:
        fee_rate = math.ceil(int(fee_rate * 1e8))

    # 😞 Determine funding address
    if not from_address:
        all_addresses = addresses.get_all_addresses()
        if not all_addresses:
            typer.echo("❌ No wallet addresses found.")
            return
        from_address = all_addresses  # 🚧 Default to first address

    result = send_evr_tx(
        to_address=to,
        from_addresses=from_address,
        amount=amount,
        dry_run=dry_run,
        debug=debug,
        raw=raw,
        fee_rate=fee_rate
    )
    if result and not raw:
        typer.echo(f"Transaction result: {result}")
        typer.echo(f"✅ Dry-run TXID: {result}")
    
    return result

# ─────────────────────────────────────
# 🔗 Send EVR Transaction
# ─────────────────────────────────────

def send_evr_tx(
    to_address: str,
    from_addresses: list,
    amount: float,
    dry_run: bool = False,
    debug: bool = False,
    raw: bool = False,
    fee_rate: int = 0
):
    from evrmail import rpc_client
    # 💼 Convert amount to satoshis
    amount_sats = int(amount * 1e8)

    tx, txid = create_send_evr_transaction(from_addresses, to_address, amount_sats, fee_rate)
    typer.echo(tx)
    result = rpc_client.testmempoolaccept([tx])
    status = result[0] if result else {}

    if dry_run:
        if raw:
            typer.echo(json.dumps({
                "txid": txid,
                "raw_tx": tx,
                "mempool_accept": status
            }, indent=2))
        else:
            if status.get("txid") == txid and status.get("allowed"):
                typer.echo("✅ Transaction accepted by testmempoolaccept ✅")
            else:
                typer.echo(f"❌ Rejected by node: {status.get('reject-reason', 'unknown reason')}")
                return None

        if debug:
            typer.echo("\n🔋 Debug Info:")
            typer.echo(f"TXID: {txid}")
            typer.echo(f"Raw TX: {tx}")

        return txid
    else:
        broadcast_result = rpc_client.sendrawtransaction(tx)
        typer.echo(f"✅ Transaction broadcasted! TXID: {broadcast_result}")
        return broadcast_result
