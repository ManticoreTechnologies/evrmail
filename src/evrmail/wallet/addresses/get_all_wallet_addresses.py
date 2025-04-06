# ─────────────────────────────────────────────────────────────
# 📬 get_all_wallet_addresses()
#
# 📌 PURPOSE:
#   Collects all addresses from all saved wallets.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.wallet.store import list_wallets, save_wallet, load_wallet

def get_all_wallet_addresses(wallet_name: str) -> list[str]:
    all_addresses = []
    wallet = load_wallet(wallet_name)
    if wallet:
        addresses = wallet.get("addresses", [])
        for addr in addresses:
            all_addresses.append(addr["address"])
    return all_addresses

