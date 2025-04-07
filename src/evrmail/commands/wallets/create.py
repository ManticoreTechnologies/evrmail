# ─────────────────────────────────────────────────────────────
# 🧱 evrmail wallets create
#
# 📌 USAGE:
#   $ evrmail wallets create <name> [-p|--pass <passphrase>] [--raw]
#
# 🛠️ DESCRIPTION:
#   Creates a new wallet using a generated mnemonic phrase.
#   An optional BIP39 passphrase can be provided for extra security.
#
#   📂 The wallet is saved to: ~/.evrmail/wallets/<name>.json
#   ⚠️  If a wallet with that name already exists, creation is aborted.
#   📄 Use --raw to get the full mnemonic and xpub in JSON
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from evrmail import wallet
from evrmail.wallet import utils

# 🚀 CLI Typer instance
create_app = typer.Typer()

# ─────────────────────────────────────────────────────────────
# 🛠️ Create Command
# ─────────────────────────────────────────────────────────────
@create_app.command(name="create", help="🛠️  Create a new wallet (with optional passphrase)")
def create(
    name: str,
    passphrase: str = typer.Option("", "--pass", "-p", help="🔐 Optional passphrase for the mnemonic"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output wallet details in raw JSON")
):
    # 🔍 Check if wallet already exists
    if wallet.load_wallet(name) is not None:
        typer.echo(f"⚠️  Wallet `{name}` already exists.")
        return 

    # 🧠 Generate mnemonic & 🔐 create wallet object
    mnemonic = utils.generate_mnemonic()
    new_wallet = wallet.create_wallet(mnemonic, passphrase)

    # 💾 Save wallet to disk
    wallet.save_wallet(name, new_wallet)

    # ✅ Output
    if raw:
        typer.echo(json.dumps({
            "name": name,
            "mnemonic": mnemonic,
            "xpub": new_wallet.xpublic_key(),
            "path": f"{wallet.WALLET_DIR}/{name}"
        }, indent=2))
    else:
        typer.echo(f"✅ Wallet `{name}` created and saved @ {wallet.WALLET_DIR}/{name}")
