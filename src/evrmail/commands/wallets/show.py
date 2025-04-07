# ─────────────────────────────────────────────────────────────
# 📄 evrmail wallets show
#
# 📌 USAGE:
#   $ evrmail wallets show <name> [--raw] [--with-addresses] [--summary]
#
# 🛠️ DESCRIPTION:
#   Display metadata for a specific wallet by name.
#   This includes xpub/xprv (truncated), creation date,
#   first derived address, and wallet file path.
#
#   Options:
#     --raw             Print full wallet data as JSON
#     --with-addresses  Show the first 5 derived addresses
#     --summary         Show EVR balance summary (requires balance module)
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import os
import json
from hdwallet.derivations import BIP44Derivation
from evrmail.wallet.utils import load_wallet, WALLET_DIR
from evrmail.wallet import addresses, rpc_client

# 🚀 CLI Subcommand
show_app = typer.Typer()

@show_app.command("show", help="📄 Show metadata for a specific wallet")
def show_wallet(
    name: str,
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON"),
    with_addresses: bool = typer.Option(False, "--with-addresses", help="📬 Show first 5 derived addresses"),
    summary: bool = typer.Option(False, "--summary", help="📊 Show balance summary"),
):
    """📄 Display metadata and info for a specific wallet."""
    try:
        data = load_wallet(name)
    except FileNotFoundError:
        typer.echo("❌ Wallet not found.")
        return

    if raw:
        typer.echo(json.dumps(data, indent=2))
        return

    # 🧾 Display wallet metadata
    typer.echo(f"\n📄 Wallet:         {data.get('name', name)}")
    typer.echo(f"📅 Created:        {data.get('created_at', 'unknown')}")
    typer.echo(f"📬 First Address:  {data.get('first_address', '-')}")
    typer.echo(f"🔑 Root xpub:      {data.get('root_xpub', '')[:16]}...")
    typer.echo(f"🔒 Root xprv:      {data.get('root_xprv', '')[:16]}...")

    # 🔐 Security Notice
    typer.echo("\n🔐 Mnemonic and passphrase are securely stored but not shown here.")

    # 📁 File path info
    typer.echo(f"💾 Wallet Path:    {os.path.join(WALLET_DIR, f'{name}.json')}")

    # 📬 Optional: Show first 5 derived addresses
    if with_addresses:
        addrs = addresses.get_all_wallet_addresses(name)
        if addrs:
            typer.echo("\n📬 First 5 Addresses:")
            for i, addr in enumerate(addrs[:5]):
                typer.echo(f"  {i+1:>2}. {addr}")
        else:
            typer.echo("❌ No derived addresses found.")

    # 📊 Optional: Show balance summary
    if summary:
        addrs = addresses.get_all_wallet_addresses(name)
        if not addrs:
            typer.echo("⚠️  Cannot compute balance summary — no addresses found.")
            return
        result = rpc_client.getaddressbalance({"addresses": addrs})
        balance = result.get("balance", 0) / 1e8
        received = result.get("received", 0) / 1e8
        typer.echo(f"\n📊 Balance Summary:")
        typer.echo(f"  ├─ Total Balance:   {balance:,.8f} EVR")
        typer.echo(f"  └─ Total Received:  {received:,.8f} EVR")
