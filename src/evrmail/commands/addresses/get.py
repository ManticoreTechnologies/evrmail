# ─────────────────────────────────────────────────────────────
# 🔢 evrmail addresses get
#
# 📌 USAGE:
#   $ evrmail addresses get --wallet <name> --index <i>
#   $ evrmail addresses get --outbox <asset>
#   $ evrmail addresses get --address <addr>
#   $ evrmail addresses get --raw ...
#
# 🛠️ DESCRIPTION:
#   Lookup address information:
#   - Get address by wallet + index
#   - Resolve public key info from asset outbox
#   - Show metadata for a specific address
#   - Combine with --raw to dump JSON
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail.wallet import utils, load_wallet

# 🚀 CLI App
get_app = typer.Typer()
__all__ = ["get_app"]

# ─────────────────────────────────────────────────────────────
# 🔢 Get Address Command
# ─────────────────────────────────────────────────────────────
@get_app.command(name="get", help="🔎 Get address info by wallet, index, or outbox")
def get(
    index: int = Option(None, "--index", help="🔢 Index within the wallet"),
    wallet: str = Option(None, "--wallet", help="👛 Wallet to pull address from"),
    outbox: str = Option(None, "--outbox", help="📦 Outbox asset (e.g., EVRMAIL#PHOENIX)"),
    address: str = Option(None, "--address", help="🏷️ Get metadata for a specific address"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """🔍 Fetch address information using wallet+index, outbox, or direct address lookup."""

    result = None

    # 📦 Lookup by Outbox Asset
    if outbox:
        result = utils.get_address_info_by_address(utils.get_address_by_asset(outbox))

    # 🏷️ Lookup by direct address
    elif address:
        result = utils.get_address_info_by_address(address)

    # 🔢 Index + Wallet lookup
    elif wallet and index is not None:
        result = {
            "wallet": wallet,
            "index": index,
            "address": utils.get_address_by_index(wallet, index),
            "path": utils.get_derivation_path(wallet, index),
            "public_key": utils.get_public_key(wallet, index),
        }

    # ❌ Invalid input
    else:
        typer.echo("❌ Provide either --outbox, --wallet + --index, or --address")
        raise typer.Exit(code=1)

    # 📄 Raw JSON
    if raw:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo("\n📬 Address Info:")
        for key, value in result.items():
            typer.echo(f"  ├─ {key}: {value}")
