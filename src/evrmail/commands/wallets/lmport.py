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
from evrmail.wallet.store import restore_wallet as restore_wallet_file

# 🚀 Typer CLI app
import_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📤 Wallet Import Command
# ─────────────────────────────────────────────────────────────
@import_app.command("import", help="📥 Import wallet from file")
def import_wallet(path: str=typer.Option(None, "--path", help="📁 Path to the backup file"), mnemonic: str=typer.Option(None, "--mnemonic", help="Mnemonic to restore the wallet"), passphrase: str=typer.Option(None, "--passphrase", help="Passphrase to restore the wallet")):
    """📥 Import a wallet from a backup file (JSON)."""
    if mnemonic and path:
        typer.echo("❌ Cannot provide both path and mnemonic")
        raise typer.Exit(1)
    if path:
        try:
            restore_wallet_file(path)
            typer.echo(f"✅ Wallet imported successfully from: {path}")
        except Exception as e:
            typer.echo(f"❌ Failed to import wallet: {e}")
    elif mnemonic:
        try:
            if passphrase:
                restore_wallet_file(mnemonic=mnemonic, passphrase=passphrase)
            else:
                restore_wallet_file(mnemonic)
            typer.echo(f"✅ Wallet imported successfully from mnemonic")
        except Exception as e:
            typer.echo(f"❌ Failed to import wallet: {e}")
