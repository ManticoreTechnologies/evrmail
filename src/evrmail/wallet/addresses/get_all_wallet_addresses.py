# ──────────────────────────────────────────────────────────
# 📌 get_all_wallet_addresses()
#
# 📌 PURPOSE:
#   Collects all addresses from a specific saved wallet.
# ──────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.wallet.store import load_wallet

def get_all_wallet_addresses(wallet_name: str, include_meta: bool = False) -> list:
    """
    📃 Returns all addresses from the given wallet.

    If include_meta=True, returns full address metadata dicts.
    Otherwise, returns a list of address strings.
    """
    all_addresses = []
    wallet = load_wallet(wallet_name)
    if wallet:
        address_dict = wallet.get("addresses", {})
        for addr_data in address_dict.values():
            if include_meta:
                addr_data["wallet"] = wallet_name  # Annotate with wallet name
                all_addresses.append(addr_data)
            else:
                all_addresses.append(addr_data["address"])
    return all_addresses
