# ─────────────────────────────────────────────────────────────
# ✅ evrmail addresses validate
#
# 📌 USAGE:
#   $ evrmail addresses validate <EVR_ADDRESS>
#   $ evrmail addresses validate <EVR_ADDRESS> --raw
#
# 🛠️ DESCRIPTION:
#   Validate whether an input string is a valid Evrmore address.
#   - Outputs status in human-readable or raw JSON form.
#   - Shows network (main/test), address version, script type, and decoded hash160.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from typer import Option, Argument
from evrmail import wallet
from evrmail.wallet.addresses.get_address import get_address

# 🚀 CLI App Instance
validate_app = typer.Typer()
__all__ = ["validate_app"]

# ─────────────────────────────────────────────────────────────
# 🧪 Validate Address
# ─────────────────────────────────────────────────────────────
@validate_app.command(name="validate", help="✅ Validate any Evrmore address")
def validate(
    address: str = Argument(..., help="🎯 Address to validate"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON")
):
    """✅ Check if an address is valid and return decoded info."""
    try:
        address_info = wallet.addresses.validate(address)
        if not address_info['isvalid']:
            raise Exception("Invalid address")

        output = {
            "address": address_info["address"],
            "valid": address_info["isvalid"],
            "script_type": "witness" if address_info["iswitness"] else ("script" if address_info["isscript"] else "pubkey"),
            "scriptPubKey": address_info.get("scriptPubKey", "-"),
            "mine": address_info.get("ismine", False),
            "watchonly": address_info.get("iswatchonly", False),
            "compressed": address_info.get("iscompressed", False),
        }

        if address_info.get("ismine"):
            extra = get_address(address)
            if extra:
                output.update({
                    "index": extra.get("index"),
                    "path": extra.get("path"),
                    "wallet": extra.get("wallet"),
                    "friendly_name": extra.get("friendly_name"),
                    "public_key": extra.get("public_key"),
                    "private_key": extra.get("private_key")
                })

        if raw:
            typer.echo(json.dumps(output, indent=2))
        else:
            typer.echo("\n✅ Address is valid!\n")
            typer.echo(f"  📬 Address       : {output['address']}")
            typer.echo(f"  🧱 Script Type   : {output['script_type']}")
            typer.echo(f"  🔐 Is Mine       : {'✅' if output['mine'] else '❌'}")
            typer.echo(f"  👀 Watch-only    : {'✅' if output['watchonly'] else '❌'}")
            typer.echo(f"  🗜️ Compressed     : {'✅' if output['compressed'] else '❌'}")
            typer.echo(f"  🧾 ScriptPubKey  : {output['scriptPubKey']}")

            if output.get("wallet"):
                typer.echo("\n🔒 Wallet Info:")
                typer.echo(f"  💼 Wallet        : {output['wallet']}")
                typer.echo(f"  🏷️  Friendly Name : {output.get('friendly_name', '-')}")
                typer.echo(f"  🔢 Index         : {output.get('index', '-')}")
                typer.echo(f"  🧭 Path          : {output.get('path', '-')}")
                typer.echo(f"  🔓 Public Key    : {output.get('public_key', '-')}")
                typer.echo(f"  🔑 Private Key   : {output.get('private_key', '-')}")

    except Exception as e:
        if raw:
            typer.echo(json.dumps({
                "address": address,
                "valid": False,
                "error": str(e)
            }, indent=2))
        else:
            typer.echo(f"❌ {e}")
