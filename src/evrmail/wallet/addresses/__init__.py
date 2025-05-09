# ─────────────────────────────────────────────────────────────
# 🧠 evrmail.wallet.addresses
#
# 📌 PURPOSE:
#   Utility functions for working with Evrmore addresses:
#   - Fetch public keys
#   - List addresses
#   - Validate addresses (Base58 + Bech32)
# ─────────────────────────────────────────────────────────────


# 📦 Imports
from .get_all_addresses import get_all_addresses
from .get_public_key_for_address import get_public_key_for_address
from .validate import validate
from .get_all_wallet_addresses import get_all_wallet_addresses
from .get_outbox_address import get_outbox_address
from .get_new_address import get_new_address

def create_new_receive_address(wallet_name=None, friendly_name=None):
    """
    Generate a new receive address for a wallet, optionally with a friendly name.
    Returns a dict with address info or error: {"success": True/False, "address": "...", "error": "..."}
    """
    import random
    from evrmail.wallet import store
    
    try:
        # Pick a wallet if not provided
        if not wallet_name:
            wallets = store.list_wallets()
            if not wallets:
                return {"success": False, "error": "No wallets found."}
            wallet_name = random.choice(wallets)
        
        # Get the new address
        if friendly_name:
            address = get_new_address(wallet_name, friendly_name)
        else:
            address = get_new_address(wallet_name)
        
        # Ensure address data is valid
        if not address or not isinstance(address, dict) or "address" not in address:
            return {"success": False, "error": "Failed to generate address"}
        
        # Return a standardized successful result
        return {
            "success": True, 
            "address": address["address"],
            "friendly_name": address.get("friendly_name", ""),
            "public_key": address.get("public_key", ""),
            "wallet": wallet_name
        }
        
    except Exception as e:
        # Return a standardized error result
        return {"success": False, "error": str(e)}

__all__ = [
    "get_all_addresses", 
    "get_public_key_for_address", 
    "validate",
    "get_all_wallet_addresses",
    "get_outbox_address",
    "get_new_address",
    "create_new_receive_address"
    ]   



