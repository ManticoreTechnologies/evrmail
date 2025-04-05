# ─────────────────────────────────────────────────────────────
# 💰 evrmail wallet balance
#
# 📌 USAGE:
#   $ evrmail wallet balance [--asset <asset>] [--assets]
#   $ evrmail wallet balance --wallet <wallet>
#   $ evrmail wallet balance --address <address>
#
# 🛠️ DESCRIPTION:
#   Displays EVR or asset balances across wallet addresses.
#   ─ If --asset is provided, shows balance for that asset.
#   ─ If --assets is used, shows all asset balances.
#   ─ If --wallet is provided, only that wallet is checked.
#   ─ If --address is used, only that address is checked.
#   ─ Defaults to all wallets if none are specified.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
from evrmore_rpc import EvrmoreClient
from evrmail.wallet.addresses import get_all_addresses
from evrmail.wallet.utils import load_wallet

# 🧠 Initialize CLI + RPC
balance_app = typer.Typer()
rpc_client = EvrmoreClient()

# ─────────────────────────────────────────────────────────────
# 📊 Balance Command
# ─────────────────────────────────────────────────────────────
@balance_app.command("balance")
def wallet_balance(
    asset: str = typer.Option(None, "--asset", help="🎯 Query balance of a specific asset"),
    assets: bool = typer.Option(False, "--assets", help="📦 Show all asset balances instead of EVR"),
    wallet: str = typer.Option(None, "--wallet", help="👛 Show balance for a specific wallet"),
    address: str = typer.Option(None, "--address", help="🏷️ Show balance for a specific address")
):
    """💳 Show EVR or asset balances from selected sources."""

    # 📬 Determine target addresses
    if address:
        target_addresses = [address]
    elif wallet:
        try:
            w = load_wallet(wallet)
            target_addresses = [entry["address"] for entry in w.get("addresses", [])]
        except Exception:
            typer.echo(f"❌ Failed to load wallet: {wallet}")
            return
    else:
        target_addresses = get_all_addresses()

    if not target_addresses:
        typer.echo("⚠️  No addresses found.")
        return

    try:
        # ── 🧮 Specific Asset Balance ─────────────────────────
        if asset:
            asset_balances = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
            total = sum(int(a.get("balance", 0)) for a in asset_balances if a["assetName"] == asset)
            formatted_total = total / 1e8
            typer.echo(f"\n🎯 Balance of asset '{asset}': {formatted_total:,.8f} units")

        # ── 📦 All Assets Summary ─────────────────────────────
        elif assets:
            balance_info = rpc_client.getaddressbalance({"addresses": target_addresses}, True)
            asset_summary = {}
            for a in balance_info:
                name = a["assetName"]
                qty = int(a["balance"])
                asset_summary[name] = asset_summary.get(name, 0) + qty

            if not asset_summary:
                typer.echo("❌ No assets found.")
                return

            typer.echo("\n📦 Asset balances:")
            for name, qty in sorted(asset_summary.items()):
                formatted_qty = qty / 1e8
                typer.echo(f"  ├─ {name}: {formatted_qty:,.8f} units")

        # ── 🪙 EVR Balance ─────────────────────────────────────
        else:
            balance_info = rpc_client.getaddressbalance({"addresses": target_addresses})
            balance = balance_info.get("balance", 0)
            received = balance_info.get("received", 0)

            formatted_balance = balance / 1e8
            formatted_received = received / 1e8

            label = (
                f"wallet `{wallet}`" if wallet else
                f"address `{address}`" if address else
                "all wallets"
            )

            typer.echo(f"\n💳 EVR balance for {label}:")
            typer.echo(f"  ├─ Current Balance: {formatted_balance:,.8f} EVR")
            typer.echo(f"  └─ Total Received: {formatted_received:,.8f} EVR")

    except Exception as e:
        typer.echo(f"❌ Failed to fetch balance: {e}")
