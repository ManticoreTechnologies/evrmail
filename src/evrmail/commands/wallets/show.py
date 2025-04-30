# ────────────────────────────────────────────────────────
# 📄 evrmail wallets show
#
# 📜 USAGE:
#   $ evrmail wallets show <name> [--raw] [--with-addresses] [--summary]
#   $ evrmail wallets show             ← shows overview of all wallets
#
# 🚰 DESCRIPTION:
#   Display metadata for a specific wallet by name.
#   Or show a summary of all wallets if no name is provided.
#   Options:
#     --raw             Print full wallet data as JSON
#     --with-addresses  Show the first 5 derived addresses
#     --summary         Show EVR balance summary (requires balance module)
# ────────────────────────────────────────────────────────

# 📆 Imports
import typer
import os
import json
from hdwallet.derivations import BIP44Derivation
from evrmail.wallet import store

# 🚀 CLI Subcommand
show_app = typer.Typer()

@show_app.command("show", help="📄 Show metadata for a specific wallet or summary of all wallets")
def show_wallet(
    name: str = typer.Argument(None, help="💼 Wallet name to inspect (omit for summary)"),
    raw: bool = typer.Option(False, "--raw", help="📄 Output raw JSON"),
    with_addresses: bool = typer.Option(False, "--with-addresses", help="📜 Show first 5 derived addresses"),
    summary: bool = typer.Option(False, "--summary", help="📈 Show EVR balance summary"),
):
    """📄 Display wallet metadata or overview of all wallets.
    """
    from evrmail import rpc_client
    if name is None:
        # 🔍 No name provided — show wallet overview
        all_wallets = store.list_wallets()
        if not all_wallets:
            typer.echo("❌ No wallets found.")
            raise typer.Exit()

        total_addresses = 0
        typer.echo("\n📆 All Wallets Summary:\n")
        for w in all_wallets:
            wallet = store.load_wallet(w)
            addr_count = len(wallet.get("addresses", {}))
            total_addresses += addr_count
            typer.echo(f"  - {w}: {addr_count} addresses")

        typer.echo(f"\n💶 Total addresses: {total_addresses}")

        if summary:
            all_addresses = []
            for w in all_wallets:
                wallet = store.load_wallet(w)
                all_addresses.extend(wallet.get("addresses", {}).keys())
            if not all_addresses:
                typer.echo("⚠️  No addresses found across wallets.")
                return
            result = rpc_client.getaddressbalance({"addresses": all_addresses})
            balance = result.get("balance", 0) / 1e8
            received = result.get("received", 0) / 1e8
            typer.echo(f"\n📈 Combined Balance Summary:")
            typer.echo(f"  ├─ Total Balance:   {balance:,.8f} EVR")
            typer.echo(f"  └─ Total Received:  {received:,.8f} EVR")
        return

    # 🔍 Load specific wallet
    try:
        data = store.load_wallet(name)
    except FileNotFoundError:
        typer.echo("❌ Wallet not found.")
        return

    if raw:
        typer.echo(json.dumps(data, indent=2))
        return

    # 📟 Display wallet metadata
    typer.echo(f"\n📄 Wallet:         {data.get('name', name)}")
    typer.echo(f"📅 Created:        {data.get('created_at', 'unknown')}")
    typer.echo(f"📜 First Address:  {next(iter(data.get('addresses', {})), '-')}")
    typer.echo(f"🔑 xpub:           {data.get('extended_public_key', '')[:16]}...")
    typer.echo(f"🔒 xprv:           {data.get('extended_private_key', '')[:16]}...")

    # 🔐 Security Notice
    typer.echo("\n🔐 Mnemonic and passphrase are securely stored but not shown here.")

    # 📋 File path info
    typer.echo(f"🛏️ Wallet Path:    {os.path.join(store.WALLET_DIR, f'{name}.json')}")

    # 📈 Address count
    addr_total = len(data.get("addresses", {}))
    typer.echo(f"💶 Total Addresses: {addr_total}")

    # 📜 Optional: Show first 5 derived addresses
    if with_addresses:
        addrs = list(data.get("addresses", {}).keys())
        if addrs:
            typer.echo("\n📜 First 5 Addresses:")
            for i, addr in enumerate(addrs[:5]):
                typer.echo(f"  {i+1:>2}. {addr}")
        else:
            typer.echo("❌ No derived addresses found.")

    # 📈 Optional: Show balance summary
    if summary:
        addrs = list(data.get("addresses", {}).keys())
        if not addrs:
            typer.echo("⚠️  Cannot compute balance summary — no addresses found.")
            return
        result = rpc_client.getaddressbalance({"addresses": addrs})
        balance = result.get("balance", 0) / 1e8
        received = result.get("received", 0) / 1e8
        typer.echo(f"\n📈 Balance Summary:")
        typer.echo(f"  ├─ Total Balance:   {balance:,.8f} EVR")
        typer.echo(f"  └─ Total Received:  {received:,.8f} EVR")