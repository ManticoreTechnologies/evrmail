# ─────────────────────────────────────────────────────────────
# ⭐ evrmail addresses active
# 
# 📌 USAGE:
#   $ evrmail addresses active
#   $ evrmail addresses active --raw
#
# 🛠️ DESCRIPTION:
#   Displays the currently selected address in the Evrmail CLI.
#   - This is the default address used for signing/sending.
#   - Use `evrmail addresses use --address <addr>` to change it.
#
#   Use --raw for machine-readable JSON output.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail import wallet

# 🚀 CLI Typer App
active_app = typer.Typer()
__all__ = ["active_app"]

# ─────────────────────────────────────────────────────────────
# ⭐ Active Address Command
# ─────────────────────────────────────────────────────────────
@active_app.command(name="active", help="⭐ Show currently selected address")
def active(
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """⭐ Display the currently active address."""
    try:
        address = wallet.get_active_address()
        if not address:
            typer.echo("⚠️  No active address is set.")
            return

        if raw:
            typer.echo(json.dumps({"active_address": address}, indent=2))
        else:
            typer.echo(f"\n⭐ Active Address:\n  → {address}")
    except Exception as e:
        typer.echo(f"❌ Failed to fetch active address: {e}")
