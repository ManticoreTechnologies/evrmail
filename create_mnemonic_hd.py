from ecdsa import SigningKey, SECP256k1
from hashlib import sha256, new as hashlib_new, pbkdf2_hmac
import hmac
from mnemonic import Mnemonic
import base58
import hmac as hmaclib
import struct

# ─────────────────────────────
# 📌 Sign arbitrary message
# ─────────────────────────────
def sign_message(msg: str) -> str:
    sk = SigningKey.generate(curve=SECP256k1)
    return sk.sign(msg.encode()).hex()

# ─────────────────────────────
# 📌 Generate mnemonic
# ─────────────────────────────
def generate_mnemonic(strength: int = 128, language: str = "english") -> str:
    mnemo = Mnemonic(language)
    return mnemo.generate(strength)

# ─────────────────────────────
# 📌 Derive Evrmore wallet from mnemonic
# ─────────────────────────────
def generate_hdwallet(mnemonic: str, passphrase: str = "") -> dict:
    try:
        seed = Mnemonic.to_seed(mnemonic, passphrase)
        I = hmaclib.new(b"Bitcoin seed", seed, sha256).digest()
        master_private_key = I[:32]

        sk = SigningKey.from_string(master_private_key, curve=SECP256k1)
        vk = sk.verifying_key
        pubkey = b'\x04' + vk.to_string()

        sha = sha256(pubkey).digest()
        ripe = hashlib_new("ripemd160", sha).digest()
        prefix = b"\x00"
        checksum = sha256(sha256(prefix + ripe).digest()).digest()[:4]
        address = base58.b58encode(prefix + ripe + checksum).decode()

        result = {
            "address": address,
            "public_key": pubkey.hex(),
            "private_key": sk.to_string().hex()
        }

        print("Generated wallet:", result)  # ✅ Add this
        return result

    except Exception as e:
        print("ERROR IN generate_hdwallet:", e)  # ✅ Log exception
        raise e
