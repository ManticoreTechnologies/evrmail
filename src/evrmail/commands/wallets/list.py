# ─────────────────────────────────────────────────────────────
# 📂 evrmail wallets list
#
# 📌 USAGE:
#   $ evrmail wallets list
#
# 🛠️ DESCRIPTION:
#   Lists all saved wallets stored in ~/.evrmail/wallets.
#   Wallet files are named <wallet>.json
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import os
from evrmail.wallet import WALLET_DIR

# 🚀 Typer CLI app
list_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📄 Wallet List Command
# ─────────────────────────────────────────────────────────────
@list_app.command("list", help="📂 List all saved wallets")
def list_wallets_command():
    """📂 Show all wallet files saved under ~/.evrmail/wallets"""
    
    typer.echo("\n📁 Available Wallets:\n")

    found = False
    for fname in os.listdir(WALLET_DIR):
        if fname.endswith(".json"):
            found = True
            typer.echo(f"  ├─ 🏷️  {fname.replace('.json', '')}")
    
    if not found:
        typer.echo("  ❌ No wallets found.")
