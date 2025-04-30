from evrmail.wallet import store
from evrmail.config import load_config
import json
from pathlib import Path

MAP_DIR = store.MAP_DIR


def get_address(query: str | int, wallet_name: str = None) -> dict | None:
    """
    🔍 Look up an address by:
        - Full address (global match)
        - Index, path, or friendly name (uses global maps)

    Returns full address dict with 'wallet' field or None.
    """
    # 🌍 Global full-address search
    if isinstance(query, str) and query.startswith("E"):
        for name in store.list_wallets():
            wallet = store.load_wallet(name)
            addresses = wallet.get("addresses", {})
            if query in addresses:
                result = addresses[query]
                result["wallet"] = name
                return result
        return None

    # 🗺️ Global map lookups (index, path, name)
    def load_map(name):
        try:
            with open(MAP_DIR / f"{name}.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    if isinstance(query, int):
        index_map = load_map("by-index")
        entry = index_map.get(str(query))
    else:
        path_map = load_map("by-path")
        name_map = load_map("by-friendly-name")
        entry = path_map.get(query) or name_map.get(query)

    if not entry:
        return None

    wallet = store.load_wallet(entry["wallet"])
    address_data = wallet["addresses"].get(entry["address"])
    if address_data:
        address_data["wallet"] = entry["wallet"]
    return address_data
