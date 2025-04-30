# ─────────────────────────────────────────────────────────────
# 🔢 evrmail addresses get
#
# 📌 USAGE:
#   $ evrmail addresses get <query>
#   $ evrmail addresses get <query> --wallet <name>
#   $ evrmail addresses get <query> --raw
#
# 🛠️ DESCRIPTION:
#   Lookup address metadata using:
#     - 📬 Full Address: global match across all wallets
#     - 🔢 Index, 🧭 Path, 🏷️ Friendly Name: automatic global search via map
# ─────────────────────────────────────────────────────────────

"""
 Tested:
    - 📬 Full Address: global match across all wallets
    - 🔢 Index, 🧭 Path, 🏷️ Friendly Name: automatic global search via map
"""

# 📦 Imports
import typer
import json
from evrmail.wallet.addresses.get_address import get_address
from typer import Argument, Option

# 🚀 CLI App
get_app = typer.Typer()
__all__ = ["get_app"]

# ─────────────────────────────────────────────────────────────
# 🔢 Get Address Command
# ─────────────────────────────────────────────────────────────
@get_app.command(name="get", help="🔎 Lookup address metadata from a wallet or by full address")
def get(
    query: str = Argument(..., help="🔍 Index, address, path, or friendly name"),
    wallet: str = Option(None, "--wallet", "-w", help="👛 Wallet to search (optional, global search by default)"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """🔍 Fetch address metadata by any identifier (full global support via map)."""

    index_query = int(query) if query.isdigit() else query
    addr = get_address(index_query, wallet_name=wallet)

    if not addr:
        typer.echo(f"❌ No matching address found for: {query}")
        raise typer.Exit(1)

    if raw:
        typer.echo(json.dumps(addr, indent=2))
    else:
        typer.echo("\n📬 Address Info:\n")
        typer.echo(f"  🏷️  Friendly Name : {addr.get('friendly_name')}")
        typer.echo(f"  🔢 Index         : {addr.get('index')}")
        typer.echo(f"  🧭 Path          : {addr.get('path')}")
        typer.echo(f"  📬 Address       : {addr.get('address')}")
        typer.echo(f"  🔓 Public Key    : {addr.get('public_key')}")
        typer.echo(f"  📦 Wallet        : {addr.get('wallet')}")
