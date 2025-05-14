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
#   • evrmail logs     — View and manage logs
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
    ipfs_app,
    logs_app
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
evrmail_gui_app = typer.Typer()
@evrmail_gui_app.command(name="evrmail-gui", help="Start the EvrMail Qt-based GUI")
def start_evrmail_gui(
    nodejs: bool = typer.Option(False, "--nodejs", help="Start in nodejs development mode")
):
    from evrmail.gui.gui import start_gui  # This will start the Qt-based GUI window
    start_gui(nodejs=nodejs)

# --- Dev GUI command
@evrmail_cli_app.command(name="dev", help="Start EvrMail GUI in development mode")
def dev_gui():
    """Start the EvrMail GUI in development mode using nodejs"""
    from evrmail.gui.gui import start_gui
    start_gui(nodejs=True)

# Default GUI command when no subcommand is specified
@evrmail_cli_app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    nodejs: bool = typer.Option(False, "--nodejs", help="Start GUI in nodejs development mode")
):
    if ctx.invoked_subcommand is None:
        # If no subcommand is given, start the GUI
        from evrmail.gui.gui import start_gui
        start_gui(nodejs=nodejs)

# 📦 Register subcommands
evrmail_cli_app.add_typer(wallets_app)
evrmail_cli_app.add_typer(addresses_app)
evrmail_cli_app.add_typer(balance_app)
evrmail_cli_app.add_typer(send_app)
evrmail_cli_app.add_typer(dev_app)
evrmail_cli_app.add_typer(contacts_app)
evrmail_cli_app.add_typer(receive_app)
evrmail_cli_app.add_typer(ipfs_app)
evrmail_cli_app.add_typer(logs_app)

# ─── 🧪 ENTRYPOINT FOR `python -m evrmail.cli` ────────────────────────────────
def main():
    evrmail_cli_app()

def gui():
    evrmail_gui_app()
    