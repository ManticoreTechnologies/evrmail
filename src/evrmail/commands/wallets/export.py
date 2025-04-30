# ─────────────────────────────────────────────────────────────
# 💾 evrmail wallets export
#
# 📌 USAGE:
#   $ evrmail wallets export <name> --output <filename>
#   $ evrmail wallets export <name> --raw
#
# 🛠️ DESCRIPTION:
#   Exports a wallet's full JSON data to a file of your choice,
#   or prints it directly to stdout using --raw.
#
#   The exported data includes your mnemonic and keys.
#   🔐 Keep it private and secure!
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from evrmail.wallet import store

# 🚀 Typer CLI app
export_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 📤 Export Command
# ─────────────────────────────────────────────────────────────
@export_app.command("export", help="💾 Export wallet to file or stdout")
def export_wallet(
    name: str,
    output: str = typer.Option(None, "--output", help="📁 Output file path"),
    raw: bool = typer.Option(False, "--raw", help="📄 Print raw JSON to stdout instead of writing to file")
):
    """📤 Export a wallet's full JSON data to a file or stdout."""
    try:
        data = store.load_wallet(name)

        # 📄 Print to stdout
        if raw:
            typer.echo(json.dumps(data, indent=2))
            return

        # 💾 Write to file
        if output:
            with open(output, "w") as f:
                json.dump(data, f, indent=2)
            typer.echo(f"✅ Wallet `{name}` exported to: {output}")
        else:
            output = f"{name}_backup.json"
            with open(output, "w") as f:
                json.dump(data, f, indent=2)
            typer.echo(f"✅ Wallet `{name}` exported to: {output}")
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}")
