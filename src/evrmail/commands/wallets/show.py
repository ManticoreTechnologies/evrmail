# ─────────────────────────────────────────────────────────────
# 📄 evrmail wallets show
#
# 📌 USAGE:
#   $ evrmail wallets show <name>
#
# 🛠️ DESCRIPTION:
#   Display metadata for a specific wallet by name.
#   This includes xpub/xprv (truncated), creation date,
#   first derived address, and wallet file path.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import os
from evrmail.wallet.utils import load_wallet, WALLET_DIR

# 🚀 CLI Subcommand
show_app = typer.Typer()

@show_app.command("show", help="📄 Show metadata for a specific wallet")
def show_wallet(name: str):
    """📄 Display metadata and info for a specific wallet."""
    try:
        data = load_wallet(name)
    except FileNotFoundError:
        typer.echo("❌ Wallet not found.")
        return

    # 🧾 Display wallet metadata
    typer.echo(f"\n📄 Wallet:         {data.get('name', name)}")
    typer.echo(f"📅 Created:        {data.get('created_at', 'unknown')}")
    typer.echo(f"📬 First Address:  {data.get('first_address', '-')}")
    typer.echo(f"🔑 Root xpub:      {data.get('root_xpub', '')[:16]}...")
    typer.echo(f"🔒 Root xprv:      {data.get('root_xprv', '')[:16]}...")

    # 🔐 Security Notice
    typer.echo("\n🔐 Mnemonic and passphrase are securely stored but not shown here.")

    # 📁 File path info
    typer.echo(f"💾 Wallet Path:    {os.path.join(WALLET_DIR, f'{name}.json')}")
