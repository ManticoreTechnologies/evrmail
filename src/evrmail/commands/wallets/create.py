# ─────────────────────────────────────────────────────────────
# 🧱 evrmail wallets create
#
# 📌 USAGE:
#   $ evrmail wallets create <name> [-p|--pass <passphrase>]
#
# 🛠️ DESCRIPTION:
#   Creates a new wallet using a generated mnemonic phrase.
#   An optional BIP39 passphrase can be provided for extra security.
#
#   📂 The wallet is saved to: ~/.evrmail/wallets/<name>.json
#   ⚠️  If a wallet with that name already exists, creation is aborted.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
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
    passphrase: str = typer.Option(
        "", "--pass", "-p", help="🔐 Optional passphrase for the mnemonic"
    )
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

    # ✅ Success
    typer.echo(f"✅ Wallet `{name}` created and saved @ {wallet.WALLET_DIR}/{name}")
