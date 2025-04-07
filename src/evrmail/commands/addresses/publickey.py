# ─────────────────────────────────────────────────────────────
# 🔍 evrmail addresses publickey
#
# 📌 USAGE:
#   $ evrmail addresses publickey --address <EVR_ADDRESS>
#
# 🛠️ DESCRIPTION:
#   Retrieves the public key associated with an address,
#   if it has been seen in a transaction or saved locally.
#
#   This is useful for encryption or verifying signatures.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option
from evrmail import wallet

# 🚀 Typer CLI app
publickey_app = typer.Typer()
__all__ = ["publickey_app"]

# ─────────────────────────────────────────────────────────────
# 🔍 Public Key Lookup
# ─────────────────────────────────────────────────────────────
@publickey_app.command(name="publickey", help="🔍 Get public key for an address (if known)")
def publickey(
    address: str = Option(..., "--address", help="🎯 Address to retrieve the public key for"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON response")
):
    """🔍 Retrieve the public key associated with a known address."""
    pubkey = wallet.get_public_key(address)

    if pubkey:
        if raw:
            typer.echo(json.dumps({"address": address, "public_key": pubkey}, indent=2))
        else:
            typer.echo(f"🔑 Public key for `{address}`: {pubkey}")
    else:
        if raw:
            typer.echo(json.dumps({"address": address, "public_key": None, "error": "Not found"}, indent=2))
        else:
            typer.echo(f"❌ Public key for `{address}` not found.")
