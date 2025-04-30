# ─────────────────────────────────────────────────────────────
# ✏️ evrmail addresses rename
#
# 📌 USAGE:
#   $ evrmail addresses rename <address> <newname>
#
# 🛠️ DESCRIPTION:
#   Rename a known address to a new friendly name.
#   This updates the global map and the wallet file.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
import typer
import json
from evrmail.wallet import store
from evrmail.wallet.store import update_map_files
from evrmail.wallet.addresses.get_address import get_address

# 🚀 CLI App
rename_app = typer.Typer()

@rename_app.command("rename", help="✏️ Rename an address to a new friendly name")
def rename_address(
    address: str = typer.Argument(..., help="📬 The full address to rename (must exist globally)"),
    newname: str = typer.Argument(..., help="🏷️  The new friendly name")
):
    # 📍 Get current address data from global maps
    addr_data = get_address(address)
    if not addr_data:
        typer.echo(f"❌ Address not found: {address}")
        raise typer.Exit(1)

    wallet_name = addr_data.get("wallet")
    if not wallet_name:
        typer.echo(f"❌ Cannot resolve owning wallet for: {address}")
        raise typer.Exit(1)

    wallet = store.load_wallet(wallet_name)
    if not wallet:
        typer.echo(f"❌ Wallet '{wallet_name}' not found.")
        raise typer.Exit(1)

    # 🚫 Check if new friendly name is taken
    fname_map_path = store.MAP_DIR / "by-friendly-name.json"
    if fname_map_path.exists():
        existing_fmap = json.load(open(fname_map_path))
        if newname in existing_fmap:
            existing_entry = existing_fmap[newname]
            typer.echo(f"❌ Friendly name '{newname}' already in use (Wallet: {existing_entry['wallet']})")
            raise typer.Exit(1)

    # 📝 Update wallet file
    wallet_entry = wallet["addresses"].get(address)
    if not wallet_entry:
        typer.echo(f"❌ Address '{address}' not found in wallet '{wallet_name}'")
        raise typer.Exit(1)

    old_name = wallet_entry.get("friendly_name", "")
    wallet_entry["friendly_name"] = newname
    store.save_wallet(wallet)

    # 🗺️ Update global map
    update_map_files({
        "by-friendly-name": {
            newname: {"address": address, "wallet": wallet_name}
        }
    })

    typer.echo(f"✅ Renamed address '{address}' from '{old_name}' to '{newname}'")
