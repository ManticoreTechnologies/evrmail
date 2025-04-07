# ─────────────────────────────────────────────────────────────
# 🔓 evrmail addresses dumpprivkey
#
# 📌 USAGE:
#   $ evrmail addresses dumpprivkey --address <addr>
#   $ evrmail addresses dumpprivkey --address <addr> --raw
#
# 🛠️ DESCRIPTION:
#   Reveal the WIF private key for a given address.
#   ⚠️ Only works for addresses you control (in your wallet).
#
#   Use --raw to return JSON output.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail import wallet

# 🚀 Typer CLI App
dumpprivkey_app = typer.Typer()
__all__ = ["dumpprivkey_app"]

# ─────────────────────────────────────────────────────────────
# 🔐 Dump Private Key Command
# ─────────────────────────────────────────────────────────────
@dumpprivkey_app.command(name="dumpprivkey", help="🔓 Dump WIF private key for an address")
def dumpprivkey(
    address: str = Option(..., "--address", help="🏷️ Address to reveal the private key for"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """🔑 Dump the WIF private key for a known wallet address."""
    try:
        privkey = wallet.utils.get_private_key_for_address(address)
        wif = wallet.utils.privkey_to_wif(privkey)

        if raw:
            typer.echo(json.dumps({
                "address": address,
                "private_key": privkey,
                "wif": wif
            }, indent=2))
        else:
            typer.echo("\n🔐 Private Key Info:")
            typer.echo(f"  🏷️  Address:     {address}")
            typer.echo(f"  🔑 Private Key: {privkey}")
            typer.echo(f"  📦 WIF Format:  {wif}")

    except Exception as e:
        typer.echo(f"❌ Failed to retrieve private key: {e}")
