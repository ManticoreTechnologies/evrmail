# ─────────────────────────────────────────────────────────────
# ✍️ evrmail addresses use
#
# 📌 USAGE:
#   $ evrmail addresses use --address <EVR_ADDRESS>
#
# 🛠️ DESCRIPTION:
#   Set a default active address to use for future transactions.
#   This is stored in the config and used by other commands
#   when no --address is explicitly provided.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail import wallet

# 🚀 CLI App Init
use_app = typer.Typer()
__all__ = ["use_app"]

# ─────────────────────────────────────────────────────────────
# ✍️ Set Active Address
# ─────────────────────────────────────────────────────────────
@use_app.command(name="use", help="✍️ Set the active address")
def use(
    address: str = Option(..., "--address", help="🎯 The address to use as default"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON response")
):
    """✍️ Set the active address for EvrMail transactions."""
    wallet.set_active_address(address)

    if raw:
        typer.echo(json.dumps({
            "active_address": address,
            "status": "success"
        }, indent=2))
    else:
        typer.echo(f"✅ Active address set to `{address}`.")
