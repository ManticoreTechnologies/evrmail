
"""
evrmail wallets [COMMAND]

💼 Manage wallets and keys

Subcommand	Description
create	🛠️ Create a new wallet (with optional passphrase)
list	📂 List all saved wallets
show	📄 Show metadata for a specific wallet
export	💾 Export wallet to file
import	📥 Import wallet from file
init	🔄 Create or restore wallet from mnemonic
"""

import typer

wallets_app = typer.Typer(name="wallets", help="💼 Manage your Evrmore wallets")

from .create import create_app
from .list import list_app
from .show import show_app
from .export import export_app
from .lmport import import_app

wallets_app.add_typer(create_app)
wallets_app.add_typer(list_app)
wallets_app.add_typer(show_app)
wallets_app.add_typer(export_app)
wallets_app.add_typer(import_app)