# ─────────────────────────────────────────────────────────────
# 🏷️  evrmail.addresses
#
# 📦 Address Management Subcommands
#   - list:       Show all known addresses
#   - get:        Derive address by index or outbox
#   - active:     Show the currently selected address
#   - use:        Set the active address
#   - validate:   Validate any Evrmore address
#   - dumpprivkey: Reveal the WIF private key
#   - publickey:  Show the public key for an address
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer

# 🚀 Root CLI Group for addresses
addresses_app = typer.Typer(name="addresses", help="🏷️  Manage addresses and keys")
__all__ = ["addresses_app"]

# 📂 Subcommands
from .list import list_app
from .get import get_app
from .validate import validate_app
from .dumpprivkey import dumpprivkey_app
from .publickey import publickey_app
from .rename import rename_app

# 🔗 Register Subcommands
addresses_app.add_typer(list_app)
addresses_app.add_typer(get_app)
addresses_app.add_typer(validate_app)
addresses_app.add_typer(dumpprivkey_app)
addresses_app.add_typer(publickey_app)
addresses_app.add_typer(rename_app)