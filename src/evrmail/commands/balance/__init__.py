# ─────────────────────────────────────────────────────────
# 💰 evrmail.balance
#
# 📜 USAGE:
#   $ evrmail balance
#   $ evrmail balance --wallet <wallet_name>
#   $ evrmail balance --address <address>
#   $ evrmail balance --asset <asset_name>
#   $ evrmail balance --assets
#   $ evrmail balance --summary
#   $ evrmail balance --utxos
#   $ evrmail balance --raw
#
# 🛠️ DESCRIPTION:
#   Show balances across addresses:
#   - No options: show total EVR balance from all addresses
#   - --wallet: show balance of all addresses in a wallet
#   - --address: show balance of one address
#   - --asset: show balance of a specific asset
#   - --assets: show all asset balances
#   - --summary: wallet stats (count, txs, totals)
#   - --utxos: list unspent outputs
#   - --raw: output raw JSON
# ────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail import wallet

# 🚀 Typer App Init
balance_app = typer.Typer()
__all__ = ["balance_app"]

# ────────────────────────────────────────────────────────
# 📊 Balance Command
# ────────────────────────────────────────────────────────
@balance_app.command(name="balance", help="💳 Show EVR or asset balances")
def balance(
    wallet_name: str = Option(None, "--wallet", help="🔍 Show balance for one wallet"),
    address: str = Option(None, "--address", help="📍 Show balance for one address"),
    asset: str = Option(None, "--asset", help="🎯 Show balance of a specific asset"),
    assets: bool = Option(False, "--assets", help="📦 Show all asset balances"),
    utxos: bool = Option(False, "--utxos", help="🗾 Show all unspent outputs (UTXOs)"),
    summary: bool = Option(False, "--summary", help="📊 Show wallet statistics summary"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON response")
):
    """💳 Show EVR or asset balances from selected sources.
    """

    from evrmail import rpc_client
    # 📬 Select Target Addresses
    if address:
        target_addresses = [address]
    elif wallet_name:
        target_addresses = wallet.addresses.get_all_wallet_addresses(wallet_name)
    else:
        target_addresses = wallet.addresses.get_all_addresses()

    # ❌ No addresses found
    if not target_addresses:
        typer.echo("⚠️  No addresses found.")
        return

    try:
        # ── 📄 Raw JSON Mode ────────────────────────────────
        if raw:
            if utxos:
                result = rpc_client.getaddressutxos({"addresses": target_addresses})
                typer.echo(json.dumps(result, indent=2))
                return
            elif summary:
                result = rpc_client.getaddressbalance({"addresses": target_addresses})
                summary_data = {
                    "address_count": len(target_addresses),
                    "balance": result.get("balance", 0),
                    "received": result.get("received", 0)
                }
                typer.echo(json.dumps(summary_data, indent=2))
                return
            elif asset:
                balances = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
                matching = [b for b in balances if b.get("assetName") == asset]
                typer.echo(json.dumps(matching, indent=2))
                return
            elif assets:
                balances = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
                typer.echo(json.dumps(balances, indent=2))
                return
            else:
                response = rpc_client.getaddressbalance({"addresses": target_addresses})
                typer.echo(json.dumps(response, indent=2))
                return

        # ── 🗾 Show UTXOs ──────────────────────────────
        if utxos:
            utxos = rpc_client.getaddressutxos({"addresses": target_addresses})
            typer.echo("\n🗾 Unspent Outputs:")
            for u in utxos:
                amt = u.get("satoshis", 0) / 1e8
                typer.echo(f"  ├─ {u['txid']}:{u['outputIndex']} — {amt:,.8f} EVR")
            return

        # ── 📊 Summary ───────────────────────────────
        if summary:
            result = rpc_client.getaddressbalance({"addresses": target_addresses})
            received = result.get("received", 0) / 1e8
            balance = result.get("balance", 0) / 1e8
            typer.echo("\n📊 Wallet Summary:")
            typer.echo(f"  - Address Count: {len(target_addresses)}")
            typer.echo(f"  - Total Balance: {balance:,.8f} EVR")
            typer.echo(f"  - Total Received: {received:,.8f} EVR")
            return

        # ── 📦 All Asset Balances ─────────────────────────────
        if assets:
            balances = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
            if not balances:
                typer.echo("❌ No asset balances found.")
                return
            typer.echo("\n📦 Asset Balances:")
            for b in balances:
                name = b.get("assetName")
                qty = int(b.get("balance", 0)) / 1e8
                typer.echo(f"  ├─ {name}: {qty:,.8f} units")

        # ── 🎯 Specific Asset Balance ──────────────────────────
        elif asset:
            balances = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
            total = 0
            for b in balances:
                if b.get("assetName") == asset:
                    total += int(b.get("balance", 0))
            formatted = total / 1e8
            typer.echo(f"\n🎯 Balance of '{asset}': {formatted:,.8f} units")

        # ── 🪙 EVR Balance ──────────────────────────────
        else:
            result = rpc_client.getaddressbalance({"addresses": target_addresses})
            evr_balance = result.get("balance", 0) / 1e8
            total_received = result.get("received", 0) / 1e8
            typer.echo(f"\n💳 Total EVR Balance:")
            typer.echo(f"  ├─ Current: {evr_balance:,.8f} EVR")
            typer.echo(f"  └─ Received: {total_received:,.8f} EVR")

    except Exception as e:
        typer.echo(f"❌ Error fetching balance: {e}")
