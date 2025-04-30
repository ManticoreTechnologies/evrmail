# ────────────────────────────────────────────────────────────
# 📌 evrmail addresses list
#
# 📌 USAGE:
#   $ evrmail addresses list
#   $ evrmail addresses list --wallet <name>
#   $ evrmail addresses list --raw
#
# 🛠️ DESCRIPTION:
#   List all known addresses:
#   - From all wallets (default)
#   - Or from a specific wallet using --wallet
#   - Optionally return results as JSON using --raw
# ────────────────────────────────────────

# 📆 Imports
from evrmail import wallet
import typer
import json
from typer import Option

# 🚀 CLI App
list_app = typer.Typer()
__all__ = ["list_app"]

# ──────────────────────────────
# 📌 List Command
# ──────────────────────────────
@list_app.command(name="list", help="📌 List all addresses with friendly names")
def list_addresses(
    wallet_name: str = Option(None, "--wallet", help="📂 List addresses from one wallet"),
    all_addresses: bool = Option(False, "--all", help="📌 List all addresses from all wallets"),
    address_count: int = Option(None, "--count", help="📌 List only the first N addresses"),
    raw: bool = Option(False, "--raw", help="📄 Output raw JSON response")
):
    """📃 List all addresses with friendly names from all wallets or a specific one,
    excluding default 'address_*' names.
    """

    if wallet_name:
        all_addrs_raw = wallet.addresses.get_all_wallet_addresses(wallet_name, include_meta=True)
        all_addrs = [
            {"address": a["address"], "friendly_name": a.get("friendly_name", ""), "wallet": wallet_name}
            for a in all_addrs_raw if isinstance(a, dict)
        ]
        filtered = [
            entry for entry in all_addrs
            if entry.get("friendly_name") and not entry["friendly_name"].startswith("address_")
        ]
    else:
        all_addrs_raw = wallet.addresses.get_all_addresses(include_meta=True)
        all_addrs = [
            {"address": a["address"], "friendly_name": a.get("friendly_name", ""), "wallet": a.get("wallet")}
            for a in all_addrs_raw if isinstance(a, dict)
        ]
        filtered = [
            entry for entry in all_addrs
            if entry.get("friendly_name") and not entry["friendly_name"].startswith("address_")
        ]

    # 🛋️ Apply count slicing logic
    def apply_count_limit(arr):
        if address_count is not None:
            return arr[address_count:] if address_count < 0 else arr[:address_count]
        return arr

    filtered = apply_count_limit(filtered)
    all_addrs = apply_count_limit(all_addrs)

    if raw:
        typer.echo(json.dumps(all_addrs if all_addresses else filtered, indent=2))
    else:
        if all_addresses:
            typer.echo("\n📃 All Addresses:\n")
            for entry in all_addrs:
                typer.echo(f"  ├─ 📌 {entry['address']}  🏷️ {entry['friendly_name']}  💼 {entry['wallet']}")
        else:
            if not filtered:
                typer.echo("❌ No named addresses found.")
                return
            typer.echo("\n📃 Named Addresses:\n")
            for entry in filtered:
                typer.echo(f"  ├─ 📃 {entry['address']}  🏷️ {entry['friendly_name']}  💼 {entry['wallet']}")
