# ─────────────────────────────────────────────────────────────
# ✅ evrmail addresses validate
#
# 📌 USAGE:
#   $ evrmail addresses validate --address <EVR_ADDRESS>
#   $ evrmail addresses validate --address <EVR_ADDRESS> --raw
#
# 🛠️ DESCRIPTION:
#   Validate whether an input string is a valid Evrmore address.
#   - Outputs status in human-readable or raw JSON form.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
from typer import Option
from evrmail import wallet

# 🚀 CLI App Instance
validate_app = typer.Typer()
__all__ = ["validate_app"]

# ─────────────────────────────────────────────────────────────
# 🧪 Validate Address
# ─────────────────────────────────────────────────────────────
@validate_app.command(name="validate", help="✅ Validate any Evrmore address")
def validate(
    address: str = Option(..., "--address", help="🎯 Address to validate"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """✅ Check if an address is valid."""
    try:
        wallet.addresses.validate(address)
        if raw:
            typer.echo({
                "address": address,
                "valid": True
            })
        else:
            typer.echo(f"✅ Address `{address}` is valid.")
    except Exception as e:
        if raw:
            typer.echo({
                "address": address,
                "valid": False,
                "error": str(e)
            })
        else:
            typer.echo(f"❌ Invalid address: {e}")
