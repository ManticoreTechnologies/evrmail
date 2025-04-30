# ─────────────────────────────────────────────────────────────
# 📂 evrmail wallets list
#
# 📌 USAGE:
#   $ evrmail wallets list
#   $ evrmail wallets list --raw
#
# 🛠️ DESCRIPTION:
#   Lists all saved wallets stored in ~/.evrmail/wallets.
#   Wallet files are named <wallet>.json
#   Use --raw for JSON output
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import os
import json
from evrmail.wallet import store

# 🚀 Typer CLI app
list_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📄 Wallet List Command
# ─────────────────────────────────────────────────────────────
@list_app.command("list", help="📂 List all saved wallets")
def list_wallets_command(
    raw: bool = typer.Option(False, "--raw", help="📄 Output wallet list as raw JSON")
):
    """📂 Show all wallet files saved under ~/.evrmail/wallets"""

    wallet_names = [
        fname.replace(".json", "")
        for fname in os.listdir(store.WALLET_DIR)
        if fname.endswith(".json")
    ]

    if raw:
        typer.echo(json.dumps(wallet_names, indent=2))
        return

    typer.echo("\n📁 Available Wallets:\n")

    if not wallet_names:
        typer.echo("  ❌ No wallets found.")
    else:
        for name in wallet_names:
            typer.echo(f"  ├─ 🏷️  {name}")
 