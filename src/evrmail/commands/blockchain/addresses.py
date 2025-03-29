"""
Manage saved Evrmore addresses.

You can receive mail to any saved address.

Commands:
  evrmail addresses add <address> --friendly-name=<optional_friendly_name>
  evrmail addresses remove <address or friendly_name>
  evrmail addresses list 
  evrmail addresses use <address or friendly_name or None>
"""

import typer
from evrmail.config import load_config, save_config
from evrmail.utils.get_privkey import get_privkey
from evrmail.utils.get_pubkey import get_pubkey

addresses_app = typer.Typer()

@addresses_app.command("add")
def add(
    address: str,
    friendly_name: str = typer.Option(None, "--friendly-name", "-f", help="A friendly name for the address")
):
    """Add a new Evrmore address to your config."""
    config = load_config()
    addresses = config.setdefault("addresses", {})

    if address in addresses:
        typer.echo("⚠️ Address already exists.")
        raise typer.Exit(1)

    pubkey = get_pubkey(address)
    privkey = get_privkey(address)

    addresses[address] = {
        "friendly_name": friendly_name,
        "pubkey": pubkey,
        "privkey": privkey,
    }

    save_config(config)
    typer.echo(f"✅ Added address: {address} ({friendly_name or 'no name'})")


@addresses_app.command("remove")
def remove(identifier: str):
    """Remove an address by address or friendly name."""
    config = load_config()
    addresses = config.get("addresses", {})
    to_delete = None

    for addr, data in addresses.items():
        if identifier == addr or identifier == data.get("friendly_name"):
            to_delete = addr
            break

    if to_delete:
        del addresses[to_delete]
        if config.get("active_address") == to_delete:
            config["active_address"] = None
        save_config(config)
        typer.echo(f"🗑️ Removed address: {to_delete}")
    else:
        typer.echo("❌ Address or friendly name not found.")
        raise typer.Exit(1)


@addresses_app.command("list")
def list_addresses():
    """List all saved Evrmore addresses."""
    config = load_config()
    addresses = config.get("addresses", {})
    active = config.get("active_address")

    if not addresses:
        typer.echo("🚫 No addresses saved.")
        return

    typer.echo("📬 Saved addresses:\n")
    for addr, data in addresses.items():
        mark = "🟢" if addr == active else "  "
        name = data.get("friendly_name", "no name")
        typer.echo(f"{mark} {addr} — {name}")


@addresses_app.command("use")
def use(identifier: str = typer.Argument(None, help="Address or friendly name to use, or omit to clear")):
    """Set or clear the default address."""
    config = load_config()
    addresses = config.get("addresses", {})

    if identifier is None:
        config["active_address"] = None
        typer.echo("✅ Default address cleared.")
    else:
        for addr, data in addresses.items():
            if identifier == addr or identifier == data.get("friendly_name"):
                config["active_address"] = addr
                save_config(config)
                typer.echo(f"✅ Now using: {addr}")
                return
        typer.echo("❌ Address or friendly name not found.")
        raise typer.Exit(1)

    save_config(config)
