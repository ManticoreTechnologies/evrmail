# ─────────────────────────────────────────────────────────────
# 📬 get_all_addresses()
#
# 📌 PURPOSE:
#   Collects all addresses from all saved wallets.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.wallet.store import list_wallets, save_wallet, load_wallet

def get_all_addresses() -> list[str]:
    all_addresses = []
    for name in list_wallets():
        wallet = load_wallet(name)
        if wallet:
            addresses = wallet.get("addresses", [])
            for addr in addresses:
                all_addresses.append(addr["address"])
    return all_addresses

