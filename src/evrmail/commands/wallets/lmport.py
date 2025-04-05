# ─────────────────────────────────────────────────────────────
# 📥 evrmail wallets import
#
# 📌 USAGE:
#   $ evrmail wallets import <path>
#
# 🛠️ DESCRIPTION:
#   Imports a wallet from a specified JSON backup file.
#   The file will be copied into ~/.evrmail/wallets.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
from evrmail.wallet import import_wallet as import_wallet_file

# 🚀 Typer CLI app
import_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📤 Wallet Import Command
# ─────────────────────────────────────────────────────────────
@import_app.command("import", help="📥 Import wallet from file")
def import_wallet(path: str):
    """📥 Import a wallet from a backup file (JSON)."""
    try:
        import_wallet_file(path)
        typer.echo(f"✅ Wallet imported successfully from: {path}")
    except Exception as e:
        typer.echo(f"❌ Failed to import wallet: {e}")
