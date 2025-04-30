# ─────────────────────────────────────────────────────────
# 🚀 evrmail.send.asset
#
# 📜 USAGE:
#   $ evrmail send asset --to <recipient> --asset-name <ASSET> --amount <qty>
#
# 🛠️ DESCRIPTION:
#   Send an asset to another address on the Evrmore blockchain.
#
# 🔧 OPTIONS:
#   --from        (optional) Sender address (uses all wallet addresses if omitted)
#   --to          Recipient address
#   --asset-name  Name of the asset (e.g. EVRMAIL#PHOENIX)
#   --amount      Amount of asset to send
#   --fee-rate    Fee rate in EVR per kB (default: 0.01)
#   --dry-run     Simulate the send without broadcasting
#   --debug       Show raw transaction and debug info
#   --raw         Output raw JSON (dry-run only)
# ─────────────────────────────────────────────────────────

import math
import json
import typer
from typing import Optional
from evrmore_rpc import EvrmoreClient
from evrmail.wallet.tx.create.send_asset import create_send_asset_transaction

# 🚀 Typer App Init
send_asset_app = typer.Typer()
__all__ = ["send_asset_app"]

@send_asset_app.command(name="asset", help="🎁 Send an ASSET")
def send(
    from_address: Optional[str] = typer.Option(None, "--from", help="📤 Optional sender address"),
    to: str = typer.Option(..., "--to", help="📥 Recipient address"),
    asset_name: str = typer.Option(..., "--asset-name", help="🏷️ Asset name (e.g. EVRMAIL#PHOENIX)"),
    amount: float = typer.Option(..., "--amount", help="🎁 Amount of asset to send"),
    fee_rate: float = typer.Option(0.01, "--fee-rate", help="💸 Fee rate in EVR per kB"),
    dry_run: bool = typer.Option(False, "--dry-run", help="🧪 Simulate transaction without sending"),
    debug: bool = typer.Option(False, "--debug", help="🔍 Show debug info"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON (dry-run only)")
):
    from evrmail import rpc_client
    from evrmail.wallet import addresses
    if fee_rate:
        fee_rate = math.ceil(int(fee_rate * 1e8))  # EVR → satoshis

    # 🧠 Get sender address(es)
    if not from_address:
        all_addresses = addresses.get_all_addresses()
        if not all_addresses:
            typer.echo("❌ No wallet addresses found.")
            raise typer.Exit(code=1)
        from_address = all_addresses
    try:
        result = send_asset_tx(
            to_address=to,
            from_addresses=from_address,
            asset_name=asset_name,
            amount=amount,
            dry_run=dry_run,
            debug=debug,
            raw=raw,
            fee_rate=fee_rate
        )

        if result and not raw:
            typer.echo(f"Transaction result: {result}")
            typer.echo(f"✅ Dry-run TXID: {result}")
    except Exception as e:
        print(e)



# ─────────────────────────────────────
# 📦 Send Asset TX Logic
# ─────────────────────────────────────
def send_asset_tx(
    to_address: str,
    from_addresses: list,
    asset_name: str,
    amount: float,
    dry_run: bool = False,
    debug: bool = False,
    raw: bool = False,
    fee_rate: int = 1_000_000
):
    from evrmail import rpc_client
    from evrmail.wallet import addresses
    # 🔢 Asset amounts are int (use smallest unit)
    asset_qty = int(amount*1e8)

    tx, txid = create_send_asset_transaction(
        from_addresses, to_address, asset_name, asset_qty, fee_rate
    )

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
            typer.echo("\n🔍 Debug Info:")
            typer.echo("─────────────────────────────────────")
            typer.echo(f"🆔 TXID       : {txid}")
            typer.echo(f"🧾 Raw Hex    : {tx}")
            typer.echo("─────────────────────────────────────")

        return txid

    # 🚀 Broadcast for real
    typer.echo("📡 Broadcasting asset transaction...")
    tx_hash = rpc_client.sendrawtransaction(tx)
    typer.echo(f"✅ Asset transaction sent! TXID: {tx_hash}")
    return tx_hash
