"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

# ─────────────────────────────────────────────────────────────
# 📦 evrmail.crypto
#
# 📌 PURPOSE:
#   - 📦 evrmail.crypto
# ─────────────────────────────────────────────────────────────



import base58
import base64
from hashlib import sha256
from Crypto.Hash import RIPEMD160
from coincurve import PrivateKey, PublicKey 

################################################
# Utilities
################################################
def evrmore_message_hash(message: str) -> bytes:
    """
    Double-SHA256 of:
      [varint(len(prefix)) + prefix + varint(len(message)) + message]
    prefix = b'Evrmore Signed Message:\\n'
    """
    prefix = b"Evrmore Signed Message:\n"

    def varint(n):
        if n < 253:
            return bytes([n])
        elif n < 0x10000:
            return b'\xfd' + n.to_bytes(2, 'little')
        elif n < 0x100000000:
            return b'\xfe' + n.to_bytes(4, 'little')
        else:
            return b'\xff' + n.to_bytes(8, 'little')

    data = varint(len(prefix)) + prefix + varint(len(message)) + message.encode()
    return sha256(sha256(data).digest()).digest()

def wif_to_privkey(wif: str) -> (bytes, bool):
    """
    Decode a WIF (Wallet Import Format) string.
    Returns (32-byte privkey, is_compressed)
    """
    raw = base58.b58decode_check(wif)
    if raw[0] != 0x80:
        raise ValueError("Invalid WIF prefix (expected 0x80).")
    if len(raw) == 34 and raw[-1] == 0x01:
        # compressed WIF
        return (raw[1:33], True)
    elif len(raw) == 33:
        # uncompressed WIF
        return (raw[1:], False)
    else:
        raise ValueError("Unexpected WIF length.")
    
def wif_to_pubkey(wif: str) -> bytes:
    """
    Given a WIF private key, return the corresponding public key bytes.
    Compressed if the WIF indicates compression; uncompressed otherwise.
    """
    privkey_bytes, compressed = wif_to_privkey(wif)
    pk = PrivateKey(privkey_bytes)
    pubkey_bytes = pk.public_key.format(compressed=compressed)
    return pubkey_bytes

def pubkey_to_address(pubkey: bytes) -> str:
    """
    Hash160 + base58 for Evrmore P2PKH (prefix=0x21 => 'E').
    """
    h = sha256(pubkey).digest()
    r160 = RIPEMD160.new(h).digest()
    versioned = b'\x21' + r160  # 0x21 => "E"
    checksum = sha256(sha256(versioned).digest()).digest()[:4]
    return base58.b58encode(versioned + checksum).decode()
def hex_to_wif(privkey_hex: str, compressed=True) -> str:
    prefix = b'\x80' + bytes.fromhex(privkey_hex)
    if compressed:
        prefix += b'\x01'
    checksum = sha256(sha256(prefix).digest()).digest()[:4]
    return base58.b58encode(prefix + checksum).decode()
################################################
# Sign / Verify
################################################
def sign_message(message: str, wif: str) -> str:
    """
    Produce a base64-encoded compact signature with header byte,
    matching Evrmore's `signmessage` logic exactly.
    """
    try:
        privkey_bytes, compressed = wif_to_privkey(wif)
        msg_hash = evrmore_message_hash(message)
    except Exception as e:
        wif = hex_to_wif(wif, compressed=True)  # Assuming compressed 
        privkey_bytes, compressed = wif_to_privkey(wif)
        msg_hash = evrmore_message_hash(message)
    pk = PrivateKey(privkey_bytes)
    # sign_recoverable returns a 65-byte:
    #   0..63 => sig
    #   64 => recid
    # but we want: 1-byte header + 64-byte sig
    # header = 27 + recid (+4 if compressed)
    full_sig = pk.sign_recoverable(msg_hash, hasher=None)  # 65 bytes
    sig_64 = full_sig[:64]
    recid = full_sig[64]
    header = 27 + recid
    if compressed:
        header += 4

    # Combine
    signature = bytes([header]) + sig_64
    return base64.b64encode(signature).decode('ascii')

def verify_message(address: str, signature_b64: str, message: str) -> bool:
    """
    Accept a base64 compact signature (header + 64 bytes).
    - parse header, recid, and compressed
    - recover pubkey
    - compute address
    - compare
    """
    try:
        raw = base64.b64decode(signature_b64)
        if len(raw) != 65:
            print("Invalid signature length")
            return False
        header = raw[0]
        sig_64 = raw[1:]
        if not (27 <= header <= 34):
            print("Invalid header byte")
            return False

        recid = (header - 27) & 3
        compressed = ((header - 27) >= 4)

        msg_hash = evrmore_message_hash(message)
        # Rebuild the 65-byte "recoverable" signature
        full_sig = sig_64 + bytes([recid])

        # Use coincurve to recover pubkey
        # from_signature_and_message expects:
        #  - signature (65 bytes, 64 sig + 1 recid)
        #  - message (the 32-byte hash)
        # but we want hasher=None so we skip hashing
        pubkey_bytes = PublicKey.from_signature_and_message(
            full_sig, msg_hash, hasher=None
        ).format(compressed=compressed)
        
        derived = pubkey_to_address(pubkey_bytes)
        return derived == address
    except Exception as e:
        print("Verification error:", e)
        return False
    
import hashlib

# Base58 alphabet used by Bitcoin/Evrmore (no 0, O, I, l)
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def decode_base58(address: str) -> bytes:
    """Decode a Base58Check string to bytes (version+payload) and verify checksum."""
    # 1. Convert the Base58 string to an integer
    value = 0
    for char in address:
        if char not in BASE58_ALPHABET:
            raise ValueError("Invalid Base58 character")
        value = value * 58 + BASE58_ALPHABET.index(char)
    # 2. Convert integer to bytes (big-endian), accounting for leading zeros (1's in Base58)
    # Count leading '1's (each represents a 0x00 byte)
    leading_ones = 0
    for ch in address:
        if ch == '1':
            leading_ones += 1
        else:
            break
    # big-endian byte array of the value
    result = value.to_bytes((value.bit_length() + 7) // 8, 'big') or b'\x00'
    # add back leading zero bytes
    result = b'\x00' * leading_ones + result
    # 3. Split into payload and checksum
    if len(result) < 4:
        raise ValueError("Invalid Base58 data (too short)")
    data, checksum = result[:-4], result[-4:]
    # 4. Compute checksum of data and compare
    check = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    if check != checksum:
        raise ValueError("Base58 checksum mismatch")
    return data  # returns version+payload bytes if valid

def decode_bech32(addr: str):
    """Decode a Bech32 SegWit address. Returns (hrp, version, program_bytes)."""
    # Bech32 addresses are case-insensitive but cannot mix case
    if addr != addr.lower() and addr != addr.upper():
        raise ValueError("Bech32 string uses mixed case")
    addr = addr.lower()
    # Split HRP and data by the last '1'
    if addr.rfind('1') == -1:
        raise ValueError("Bech32 format error (no separator)")
    hrp, data_part = addr[:addr.rfind('1')], addr[addr.rfind('1')+1:]
    if len(hrp) == 0 or len(data_part) < 6:
        raise ValueError("Bech32 format error (HRP or data too short)")
    # Bech32 character set mapping
    BECH32_CHARS = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    # 1. Convert data part from base32 (5 bits per char) to list of integers
    data_values = []
    for char in data_part:
        if char not in BECH32_CHARS:
            raise ValueError("Invalid Bech32 character")
        data_values.append(BECH32_CHARS.index(char))
    # 2. Verify the checksum using polymod
    def polymod(values):
        """Compute Bech32 checksum polynomial."""
        GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
        chk = 1
        for v in values:
            top = chk >> 25
            chk = (chk & 0x1FFFFFF) << 5 ^ v
            for i in range(5):
                if (top >> i) & 1:
                    chk ^= GEN[i]
        return chk
    # Expand HRP (each char to high bits and low bits) and combine with data
    hrp_expand = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 0x1F for x in hrp]
    if polymod(hrp_expand + data_values) != 1:
        raise ValueError("Bech32 checksum failed")
    # 3. Separate data values into witness version and program
    version = data_values[0]
    if version > 16:
        raise ValueError("Invalid witness version")
    # Convert 5-bit groups to 8-bit bytes (without including the last 6 checksum values)
    data = data_values[1:-6]  # actual witness program data (5-bit groups)
    # Conversion of 5-bit groups to bytes:
    bits = 0
    acc = 0
    program = bytearray()
    for value in data:
        acc = (acc << 5) | value
        bits += 5
        # Extract 8-bit bytes from accumulated bits
        while bits >= 8:
            bits -= 8
            program.append((acc >> bits) & 0xFF)
    # There should be no leftover bits that are non-zero (padding must be zero)
    if bits > 0:
        # If remaining bits represent non-zero, it's invalid padding
        if (acc << (8 - bits)) & 0xFF:
            raise ValueError("Invalid Bech32 padding")
    program_bytes = bytes(program)
    # Check program length
    if len(program_bytes) < 2 or len(program_bytes) > 40:
        raise ValueError("Invalid witness program length")
    if version == 0 and len(program_bytes) not in (20, 32):
        raise ValueError("Invalid v0 program length")
    return hrp, version, program_bytes

def validate_evr_address(address: str):
    """Validate an Evrmore address and return a dict of address details."""
    result = {"isvalid": False}
    # Try Base58 decoding
    try:
        data = decode_base58(address)
        version = data[0]
        payload = data[1:]
        # Identify address type by version byte
        if version == 33:       # 0x21, Evrmore mainnet P2PKH
            addr_type = "P2PKH"
            result["isscript"] = False
            result["iswitness"] = False
        elif version == 92:     # 0x5C, Evrmore mainnet P2SH
            addr_type = "P2SH"
            result["isscript"] = True
            result["iswitness"] = False
        elif version == 111:    # 0x6F, testnet P2PKH (m/n...)
            addr_type = "P2PKH"
            result["isscript"] = False
            result["iswitness"] = False
        elif version == 196:    # 0xC4, testnet P2SH (starts with '2')
            addr_type = "P2SH"
            result["isscript"] = True
            result["iswitness"] = False
        else:
            # Unknown prefix (not an Evrmore address)
            raise ValueError("Unknown address version")
        # Construct scriptPubKey
        hash160 = payload.hex()
        if addr_type == "P2PKH":
            # scriptPubKey: OP_DUP OP_HASH160 <hash160> OP_EQUALVERIFY OP_CHECKSIG
            script_pubkey = "76a914" + hash160 + "88ac"
        else:  # P2SH
            # scriptPubKey: OP_HASH160 <hash160> OP_EQUAL
            script_pubkey = "a914" + hash160 + "87"
        # Populate result fields for a valid address
        result["isvalid"] = True
        result["address"] = address
        result["scriptPubKey"] = script_pubkey
        result["ismine"] = False       # offline, we assume not in our wallet
        result["iswatchonly"] = False  # offline, not a watch-only wallet address
        result["iscompressed"] = False # cannot determine from address alone
        # (We could include HD fields here if available, but offline they are not.)
        return result
    except Exception:
        # Not a valid Base58 address, proceed to check Bech32
        pass
    # Try Bech32 decoding (SegWit address)
    try:
        hrp, version, program = decode_bech32(address)
        # Verify the HRP matches Evrmore (to avoid confusion with other chains)
        if hrp not in ("evr", "evrt"):
            raise ValueError("Wrong HRP for Evrmore")
        # Determine script type from witness version and program length
        if version == 0:
            # SegWit v0: P2WPKH or P2WSH
            if len(program) == 20:
                # P2WPKH (pubkey hash in witness program)
                result["isscript"] = False
            elif len(program) == 32:
                # P2WSH (script hash in witness program)
                result["isscript"] = True
            else:
                result["isscript"] = False  # (Should not happen due to earlier length check)
            # Construct scriptPubKey hex (version 0 is OP_0)
            script_pubkey = f"{version:02x}" + f"{len(program):02x}" + program.hex()
            # (OP_0 is 0x00, then pushdata of 20 or 32 bytes: 0x14 or 0x20)
        else:
            # For future versions (1-16), scriptPubKey = OP_(version) <program>
            op_n = 0x50 + version  # OP_1 = 0x51 for version=1, ... OP_16 = 0x60
            script_pubkey = f"{op_n:02x}" + f"{len(program):02x}" + program.hex()
            # Assume script if program looks like a script hash:
            result["isscript"] = (len(program) == 32)
        # Populate result for Bech32 address
        result["isvalid"] = True
        result["address"] = address
        result["scriptPubKey"] = script_pubkey
        result["iswitness"] = True
        result["witness_version"] = int(version)
        result["witness_program"] = program.hex()
        result["ismine"] = False
        result["iswatchonly"] = False
        result["iscompressed"] = False  # not applicable to script, but field included
        return result
    except Exception:
        # Not Base58 or Bech32 – invalid address
        result["isvalid"] = False
        return result

def encrypt_message(pubkey_bytes: bytes, plaintext: str) -> bytes:
    pub = PublicKey(pubkey_bytes)
    return pub.encrypt(plaintext.encode())

def decrypt_message(wif: str, ciphertext: bytes) -> str:
    privkey_bytes, _ = wif_to_privkey(wif)
    priv = PrivateKey(privkey_bytes)
    return priv.decrypt(ciphertext).decode()


__all__ = ["sign_message", "verify_message", "wif_to_privkey", "wif_to_pubkey", "pubkey_to_address", "validate_evr_address"]