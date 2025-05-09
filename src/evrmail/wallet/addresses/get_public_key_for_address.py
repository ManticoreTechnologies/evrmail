# ─────────────────────────────────────────────────────────────
# 🔍 get_public_key_for_address(address)
#
# 📌 PURPOSE:
#   Retrieves the public key for a specific address by checking
#   all saved wallets under ~/.evrmail/wallets.
# ─────────────────────────────────────────────────────────────

# 📦 Imports
from evrmail.wallet.store import list_wallets, load_wallet

def get_public_key_for_address(address: str) -> str:
    for name in list_wallets():
        wallet = load_wallet(name)
        wallet_addresses = wallet.get("addresses", [])
        for entry in wallet_addresses:
            entry_data = wallet_addresses.get(entry)
            if entry_data.get("address") == address:
                return entry_data.get("public_key")
    raise Exception(f"Public key for address {address} not found in any wallet.")
