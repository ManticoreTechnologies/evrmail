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
from evrmail.wallet import list_wallets, load_wallet
from evrmail.crypto import decode_base58, decode_bech32

# ─────────────────────────────────────────────────────────────
# 🔍 get_public_key_for_address(address)
#
# 📌 PURPOSE:
#   Retrieves the public key for a specific address by checking
#   all saved wallets under ~/.evrmail/wallets.
# ─────────────────────────────────────────────────────────────
def get_public_key_for_address(address: str) -> str:
    for name in list_wallets():
        wallet = load_wallet(name)
        for entry in wallet.get("addresses", []):
            if entry["address"] == address:
                return entry["public_key"]
    raise Exception(f"Public key for address {address} not found in any wallet.")

# ─────────────────────────────────────────────────────────────
# 📬 get_all_addresses()
#
# 📌 PURPOSE:
#   Collects all addresses from all saved wallets.
# ─────────────────────────────────────────────────────────────
def get_all_addresses() -> list[str]:
    all_addresses = []
    for name in list_wallets():
        wallet = load_wallet(name)
        if wallet:
            addresses = wallet.get("addresses", [])
            for addr in addresses:
                all_addresses.append(addr["address"])
    return all_addresses

# ─────────────────────────────────────────────────────────────
# ✅ validate(address)
#
# 📌 PURPOSE:
#   Validates an address (Base58 or Bech32) and returns:
#   - Address type
#   - Ownership
#   - ScriptPubKey
#   - Witness info if applicable
# ─────────────────────────────────────────────────────────────
def validate(address: str) -> dict:
    result = {"isvalid": False}
    my_addresses = get_all_addresses()

    # 🔍 Attempt Base58 decoding
    try:
        data = decode_base58(address)
        version = data[0]
        payload = data[1:]

        # 🧠 Detect address type by version byte
        if version == 33:       # 0x21, mainnet P2PKH
            addr_type = "P2PKH"
            result["isscript"] = False
            result["iswitness"] = False
        elif version == 92:     # 0x5C, mainnet P2SH
            addr_type = "P2SH"
            result["isscript"] = True
            result["iswitness"] = False
        elif version == 111:    # 0x6F, testnet P2PKH
            addr_type = "P2PKH"
            result["isscript"] = False
            result["iswitness"] = False
        elif version == 196:    # 0xC4, testnet P2SH
            addr_type = "P2SH"
            result["isscript"] = True
            result["iswitness"] = False
        else:
            raise ValueError("Unknown address version")

        # 🧱 Build scriptPubKey
        hash160 = payload.hex()
        script_pubkey = (
            "76a914" + hash160 + "88ac" if addr_type == "P2PKH"
            else "a914" + hash160 + "87"
        )

        # ✅ Populate validation result
        result.update({
            "isvalid": True,
            "address": address,
            "scriptPubKey": script_pubkey,
            "ismine": address in my_addresses,
            "iswatchonly": False,
            "iscompressed": False
        })
        return result

    except Exception:
        pass  # 👇 Fall through to Bech32

    # 🧪 Try Bech32 decoding
    try:
        hrp, version, program = decode_bech32(address)

        if hrp not in ("evr", "evrt"):
            raise ValueError("Wrong HRP for Evrmore")

        # 🧠 Determine script type and encoding
        if version == 0:
            if len(program) == 20:
                result["isscript"] = False  # P2WPKH
            elif len(program) == 32:
                result["isscript"] = True   # P2WSH
            else:
                result["isscript"] = False
            script_pubkey = f"{version:02x}{len(program):02x}{program.hex()}"
        else:
            op_n = 0x50 + version
            script_pubkey = f"{op_n:02x}{len(program):02x}{program.hex()}"
            result["isscript"] = (len(program) == 32)

        # ✅ Populate validation result for Bech32
        result.update({
            "isvalid": True,
            "address": address,
            "scriptPubKey": script_pubkey,
            "iswitness": True,
            "witness_version": int(version),
            "witness_program": program.hex(),
            "ismine": address in my_addresses,
            "iswatchonly": False,
            "iscompressed": False
        })
        return result

    except Exception:
        result["isvalid"] = False
        return result
