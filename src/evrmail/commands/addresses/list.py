# ─────────────────────────────────────────────────────────────
# 📬 evrmail addresses list
#
# 📌 USAGE:
#   $ evrmail addresses list
#   $ evrmail addresses list --wallet <name>
#   $ evrmail addresses list --raw
#
# 🛠️ DESCRIPTION:
#   List all known addresses:
#   - From all wallets (default)
#   - Or from a specific wallet using --wallet
#   - Optionally return results as JSON using --raw
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail import wallet
import typer
import json
from typer import Option

# 🚀 CLI App
list_app = typer.Typer()
__all__ = ["list_app"]

# ─────────────────────────────────────────────────────────────
# 📬 List Command
# ─────────────────────────────────────────────────────────────
@list_app.command(name="list", help="📬 List all addresses from all wallets")
def list_addresses(
    wallet_name: str = Option(None, "--wallet", help="📂 List addresses from one wallet"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON response")
):
    """📬 List all addresses from all wallets or a specific one."""

    if wallet_name:
        addresses = wallet.addresses.get_all_wallet_addresses(wallet_name)
    else:
        addresses = wallet.addresses.get_all_addresses()

    if raw:
        typer.echo(json.dumps(addresses, indent=2))
    else:
        if not addresses:
            typer.echo("❌ No addresses found.")
            return
        typer.echo("\n📬 Known Addresses:\n")
        for addr in addresses:
            typer.echo(f"  ├─ 📮 {addr}")
