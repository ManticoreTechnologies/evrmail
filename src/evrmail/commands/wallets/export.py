# ─────────────────────────────────────────────────────────────
# 💾 evrmail wallets export
#
# 📌 USAGE:
#   $ evrmail wallets export <name> --output <filename>
#
# 🛠️ DESCRIPTION:
#   Exports a wallet's full JSON data to a file of your choice.
#   This can be used for backup or migration purposes.
#
#   The exported file will contain mnemonic and keys, so keep it secure!
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from evrmail.wallet import WALLET_DIR, load_wallet

# 🚀 Typer CLI app
export_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📤 Export Command
# ─────────────────────────────────────────────────────────────
@export_app.command("export", help="💾 Export wallet to file")
def export_wallet(name: str, output: str):
    """📤 Export a wallet's full JSON data to a file."""
    try:
        data = load_wallet(name)
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        typer.echo(f"✅ Wallet `{name}` exported to: {output}")
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}")
