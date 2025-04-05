# ─────────────────────────────────────────────────────────────
# 🔄 evrmail wallets init
#
# 📌 USAGE:
#   $ evrmail wallets init
#
# 🛠️ DESCRIPTION:
#   Interactive command to create or restore an Evrmore wallet.
#   - If creating, generates a new 12-word mnemonic.
#   - If restoring, prompts for your own mnemonic & passphrase.
#
#   The wallet will be saved under ~/.evrmail/wallets/<name>.json
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import os
from hdwallet.derivations import BIP44Derivation
from evrmail.wallet.utils import (
    generate_mnemonic,
    WALLET_DIR,
    create_wallet,
    save_wallet,
)

# 🚀 Typer CLI app
init_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 🧠 Wallet Init Command
# ─────────────────────────────────────────────────────────────
@init_app.command("init", help="🔄 Create or restore a wallet")
def init_wallet():
    """🔐 Create or restore an Evrmore HD wallet interactively."""

    typer.echo("🔐 Evrmore Wallet Setup")
    choice = typer.prompt("Do you want to [C]reate a new wallet or [R]estore an existing one?").lower()

    # 🆕 Create
    if choice.startswith("c"):
        mnemonic = generate_mnemonic()
        typer.echo(f"\n🧠 Your new mnemonic:\n\n{mnemonic}\n")
        passphrase = typer.prompt("Set a passphrase (you'll need this to unlock the wallet)", hide_input=True)

    # ♻️ Restore
    elif choice.startswith("r"):
        mnemonic = typer.prompt("Enter your 12/24-word mnemonic")
        passphrase = typer.prompt("Enter your passphrase (if none, leave empty)", hide_input=True)

    else:
        typer.echo("❌ Invalid option. Enter 'C' to create or 'R' to restore.")
        raise typer.Abort()

    # 📛 Name the wallet
    wallet_name = typer.prompt("📝 Name this wallet (no spaces)").strip()
    wallet_file = os.path.join(WALLET_DIR, f"{wallet_name}.json")

    if os.path.exists(wallet_file):
        typer.confirm(f"⚠️ A wallet named '{wallet_name}' already exists. Overwrite?", abort=True)

    # 🧱 Build wallet
    hdwallet = create_wallet(mnemonic, passphrase)
    address_count = 10
    addresses = []

    for i in range(address_count):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)
        addr = hdwallet.address()
        addresses.append({
            "index": i,
            "path": f"m/44'/175'/0'/0/{i}",
            "address": addr,
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key()
        })
        hdwallet.clean_derivation()

    # 💾 Save wallet
    save_wallet(wallet_name, hdwallet)
    typer.echo(f"💾 Wallet saved to: {wallet_file}")
