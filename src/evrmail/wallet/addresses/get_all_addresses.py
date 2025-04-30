# ─────────────────────────────────────────────────────────────
# 📬 get_all_addresses()
#
# 📌 PURPOSE:
#   Collects all addresses from all saved wallets.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.wallet.store import list_wallets, load_wallet

def get_all_addresses(include_meta: bool = False) -> list:
    all_addresses = []
    for name in list_wallets():
        wallet = load_wallet(name)
        if wallet:
            address_dict = wallet.get("addresses", {})
            for addr_obj in address_dict.values():
                if include_meta:
                    addr_obj_with_wallet = addr_obj.copy()
                    addr_obj_with_wallet["wallet"] = name
                    all_addresses.append(addr_obj_with_wallet)
                else:
                    all_addresses.append(addr_obj["address"])
    return all_addresses
