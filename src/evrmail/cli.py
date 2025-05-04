"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EfletL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 📬 EvrMail CLI — Decentralized Email on Evrmore
# 
# A secure, blockchain-native messaging system powered by asset channels and encrypted metadata.
# 
# 🔧 Subcommands:
#   • evrmail send     — Send a message
#   • evrmail inbox    — View your messages
#   • evrmail wallet   — Manage keys and funds
#   • evrmail address  — Manage address book
#   • evrmail config   — View/set config (outbox, default address, etc.)
#   • evrmail tx       — Inspect or decode transactions
#   • evrmail debug    — Advanced developer tools
# ─────────────────────────────────────────────────────────────

# ─── 🧩 IMPORTS ────────────────────────────────────────────────────────────────
import typer
from .commands import (
    send_app,
    wallets_app,
    addresses_app,
    balance_app,
    dev_app,
    contacts_app,
    receive_app,
    ipfs_app
)

# ─── 🚀 MAIN CLI APP ───────────────────────────────────────────────────────────
evrmail_cli_app = typer.Typer(
    name="evrmail",
    help="""
📬 EvrMail - Decentralized Email on Evrmore

A secure, blockchain-native messaging system powered by asset channels and encrypted metadata.
""",
    add_completion=False,
)

# --- Sub CLI App (Gui mode)
evrmail_flet_app = typer.Typer()
@evrmail_flet_app.command(name="evrmail-flet", help="Start the gui for evrmail")
def start_evrmail_flet():
    from evrmail.gui.main import run_gui  # this should start your GUI window
    print("To be implemented!")
    run_gui()
# 📦 Register subcommands
evrmail_cli_app.add_typer(wallets_app)
evrmail_cli_app.add_typer(addresses_app)
evrmail_cli_app.add_typer(balance_app)
evrmail_cli_app.add_typer(send_app)
evrmail_cli_app.add_typer(dev_app)
evrmail_cli_app.add_typer(contacts_app)
evrmail_cli_app.add_typer(receive_app)
evrmail_cli_app.add_typer(ipfs_app)

# ─── 🧪 ENTRYPOINT FOR `python -m evrmail.cli` ────────────────────────────────
def main():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    evrmail_cli_app()

def flet():
    evrmail_flet_app()
    