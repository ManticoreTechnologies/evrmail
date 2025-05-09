# evrmail/wallet.py
import json
import os
from datetime import datetime
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.mnemonics.bip39 import BIP39Mnemonic
from hdwallet.derivations import BIP44Derivation
from mnemonic import Mnemonic
import hashlib
mnemo = Mnemonic("english")

from evrmail.wallet import (
    WALLET_DIR
)

def load_utxos():
    from evrmail.daemon.__main__ import MEMPOOL_UTXO_FILE, CONFIRMED_UTXO_FILE
    mempool = {}
    confirmed = {}
    if MEMPOOL_UTXO_FILE.exists():
        mempool = json.loads(MEMPOOL_UTXO_FILE.read_text())
    if CONFIRMED_UTXO_FILE.exists():
        confirmed = json.loads(CONFIRMED_UTXO_FILE.read_text())
    return {"mempool": mempool, "confirmed": confirmed}
def load_asset_utxos(unspent: bool = True):
    utxos = load_utxos()
    asset_utxos = {}
    for address, utxos in utxos.get("confirmed", {}).items():
        for utxo in utxos:
            if utxo.get("spent") == False:
                if utxo.get("asset") is not None:
                    asset_utxos[address] = utxo
    return asset_utxos

def get_first_outbox_utxo():
    utxos = load_asset_utxos(unspent=True)
    return utxos[list(utxos.keys())[0]]
def load_all_wallet_keys():
    # List all wallets by name
    wallets = list_wallets()
    wallet_keys = {}
    for wallet in wallets:
        wallet_keys[wallet] = load_wallet(wallet)
        del wallet_keys[wallet]['addresses']
    return wallet_keys
def wif_from_privkey(privkey_bytes: bytes, compressed: bool = True, mainnet: bool = True) -> str:
    """
    Convert raw private key bytes into WIF format for Evrmore.
    
    Parameters:
    - privkey_bytes: 32-byte private key
    - compressed: whether to encode as compressed key (default True)
    - mainnet: True for mainnet (EVR), False for testnet (tEVR)

    Returns:
    - WIF-encoded private key string
    """
    if len(privkey_bytes) != 32:
        raise ValueError("Private key must be 32 bytes")

    prefix = b'\x80' if mainnet else b'\xef'
    payload = prefix + privkey_bytes
    if compressed:
        payload += b'\x01'

    checksum = sha256(sha256(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()
def get_address_by_asset(asset: str) -> str:
    """
    Get the address for a given asset.
    """
    from evrmail import rpc_client
    addresses = rpc_client.listaddressesbyasset(asset)
    if addresses:
        return list(addresses.keys())[0]
    else:
        return None
def get_public_key(wallet: str, index: int) -> str:
    """
    Get the public key for a given index.
    """
    wallet = load_wallet(wallet)
    return wallet.get("addresses", [])[index].get("public_key")



def get_derivation_path(wallet: str, index: int) -> str:
    """
    Get the derivation path for a given index.
    """
    wallet = load_wallet(wallet)
    return wallet.get("addresses", [])[index].get("path")
import base58
from hashlib import sha256
def privkey_to_wif(privkey_hex: str, compressed: bool = True, mainnet: bool = True) -> str:
    privkey_bytes = bytes.fromhex(privkey_hex)

    prefix = b'\x80' if mainnet else b'\xef'
    payload = prefix + privkey_bytes

    if compressed:
        payload += b'\x01'

    checksum = sha256(sha256(payload).digest()).digest()[:4]
    wif = base58.b58encode(payload + checksum)
    return wif.decode()
def get_address_by_index(wallet: str, index: int) -> str:
    """
    Get the address for a given index.
    """
    wallet = load_wallet(wallet)
    return wallet.get("addresses", [])[index].get("address")

def get_address_info_by_address(address: str) -> dict:
    """
    Get the address info for a given address.
    """
    wallets = list_wallets()    
    for wallet in wallets:
        wallet = load_wallet(wallet)
        for _address in wallet.get("addresses", []):
            if _address.get("address") == address:
                return _address
    return None

def generate_mnemonic(strength: int = 128) -> str:
    if strength not in [128, 160, 192, 224, 256]:
        strength = 128
    return mnemo.generate(strength)

def create_wallet(mnemonic: str, passphrase: str = "") -> HDWallet:
    hdwallet = HDWallet(cryptocurrency=Evrmore, passphrase=passphrase)
    hdwallet.from_mnemonic(BIP39Mnemonic(mnemonic=mnemonic))
    return hdwallet

def wallet_file_path(name: str) -> str:
    return os.path.join(WALLET_DIR, f"{name}.json")

def address_to_pubkey_hash(address: str) -> bytes:
    """
    Decode a base58check Evrmore address and return the 20-byte pubkey hash (in hex).
    Supports:
      - P2PKH (version byte 0x21)
      - P2SH  (version byte 0x05)
    """
    import base58
    decoded = base58.b58decode_check(address)
    version_byte = decoded[0]
    pubkey_hash = decoded[1:]
    
    print(f"Address: {address}")
    print(f"Version byte: {version_byte} (hex: {hex(version_byte)})")
    print(f"Pubkey hash (hex): {pubkey_hash.hex()}")

    if version_byte in (0x21, 0x05):
        return pubkey_hash
    else:
        raise ValueError(f"Unsupported address version: {version_byte}")
def save_wallet(name: str, hdwallet: HDWallet, address_count: int=1000):
    addresses = []
    for i in range(address_count):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)
        addr = hdwallet.address()
        addresses.append({
            "index": i,
            "path": f"m/44'/175'/0'/0/{i}",
            "address": addr,
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key()
        })
        hdwallet.clean_derivation()
    mnemonic = hdwallet.mnemonic()
    passphrase = hdwallet.passphrase()
    wallet_data = {
        "name": name,
        "created_at": datetime.utcnow().isoformat(),
        "mnemonic": mnemonic,
        "passphrase": passphrase,
        "coin_type": 175,
        "root_xprv": hdwallet.root_xprivate_key(),
        "root_xpub": hdwallet.root_xpublic_key(),
        "first_address": addresses[0]['address'],
        "addresses": addresses
    }

    with open(wallet_file_path(name), "w") as f:
        json.dump(wallet_data, f, indent=2)

def load_wallet(name: str):
    path = wallet_file_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def list_wallets():
    return [f.replace(".json", "") for f in os.listdir(WALLET_DIR) if f.endswith(".json")]

def list_wallet_addresses(wallet_data):
    return wallet_data.get("addresses", [])

def get_private_key_for_address(address: str) -> str:
    found_address = None
    for name in list_wallets():
        wallet = load_wallet(name)
        if address in wallet['addresses']:
            found_address = wallet['addresses'][address]
    if found_address:
        return found_address['private_key']
    raise Exception(f"Private key for address {address} not found in any wallet.")

def get_public_key_for_address(address: str) -> str:
    found_address = None
    for name in list_wallets():
        wallet = load_wallet(name)
        if address in wallet['addresses']:
            found_address = wallet['addresses'][address]
    if found_address:
        return found_address['public_key']
    raise Exception(f"Public key for address {address} not found in any wallet.")
        

def set_active_address(address: str):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    config["active_address"] = address
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
def encode_pushdata(data: bytes) -> bytes:
    l = len(data)
    if l < 0x4c:
        return bytes([l]) + data
    elif l <= 0xff:
        return b'\x4c' + bytes([l]) + data  # OP_PUSHDATA1
    elif l <= 0xffff:
        return b'\x4d' + l.to_bytes(2, 'little')  # OP_PUSHDATA2
    else:
        return b'\x4e' + l.to_bytes(4, 'little')  # OP_PUSHDATA4



def serialize_signed_tx(vin, vout, locktime=0):
    version = (2).to_bytes(4, 'little')
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''
    for txin in vin:
        inputs += bytes.fromhex(txin["txid"])[::-1]
        inputs += txin["vout"].to_bytes(4, 'little')

        # Parse and include actual scriptSig
        script_sig_bytes = bytes.fromhex(txin["scriptSig"]["hex"])
        
        inputs += len(script_sig_bytes).to_bytes(1, 'little')
        inputs += script_sig_bytes

        inputs += txin["sequence"].to_bytes(4, 'little')

    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        value = int(txout["value"])
        outputs += value.to_bytes(8, 'little')
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += len(script_bytes).to_bytes(1, 'little')
        outputs += script_bytes

    locktime_bytes = locktime.to_bytes(4, 'little')

    return version + input_count + inputs + output_count + outputs + locktime_bytes

def serialize_unsigned_tx(vin, vout, locktime=0):
    version = 2 .to_bytes(4, 'little')  # Evrmore uses version 2
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''
    for txin in vin:
        inputs += bytes.fromhex(txin["txid"])[::-1]            # reverse txid
        inputs += txin["vout"].to_bytes(4, 'little')           # output index
        inputs += b'\x00'                                      # placeholder for script length (empty)
        inputs += txin["sequence"].to_bytes(4, 'little')       # sequence

    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        satoshis = int(txout["value"])
        outputs += satoshis.to_bytes(8, 'little')              # value
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += len(script_bytes).to_bytes(1, 'little')     # script length
        outputs += script_bytes

    locktime_bytes = locktime.to_bytes(4, 'little')

    return version + input_count + inputs + output_count + outputs + locktime_bytes
import json
from pathlib import Path

def calculate_balances():
    """
    Calculate EVR and Asset balances from ~/.evrmail/utxos/confirmed.json and mempool.json.

    Returns:
        {
            "evr": {"address1": total_balance, "address2": total_balance, ...},
            "assets": {
                "ASSETNAME": {"address1": qty, "address2": qty, ...},
                ...
            }
        }
    """
    STORAGE_DIR = Path.home() / ".evrmail"
    UTXO_DIR = STORAGE_DIR / "utxos"
    CONFIRMED_FILE = UTXO_DIR / "confirmed.json"
    MEMPOOL_FILE = UTXO_DIR / "mempool.json"

    balances = {
        "evr": {},
        "assets": {}
    }

    # Helper to add a UTXO into balances
    def add_utxo_to_balance(addr, asset_name, amount):
        if asset_name is None:
            balances["evr"][addr] = balances["evr"].get(addr, 0) + amount
        else:
            if asset_name not in balances["assets"]:
                balances["assets"][asset_name] = {}
            balances["assets"][asset_name][addr] = balances["assets"][asset_name].get(addr, 0) + amount

    # Load from confirmed UTXOs
    if CONFIRMED_FILE.exists():
        confirmed = json.loads(CONFIRMED_FILE.read_text())
        for address, utxos in confirmed.items():
            for utxo in utxos:
                if utxo.get("spent", False):
                    continue
                add_utxo_to_balance(address, utxo.get("asset"), utxo.get("amount", 0))

    # Load from mempool UTXOs (unconfirmed)
    if MEMPOOL_FILE.exists():
        mempool = json.loads(MEMPOOL_FILE.read_text())
        for address, utxos in mempool.items():
            for utxo in utxos:
                if utxo.get("spent", False):
                    continue
                add_utxo_to_balance(address, utxo.get("asset"), utxo.get("amount", 0))

    return balances


def get_sighash(vin, vout, input_index, script_pubkey_hex, locktime=0):
    version = 2 .to_bytes(4, 'little')
    input_count = len(vin).to_bytes(1, 'little')
    inputs = b''

    for i, txin in enumerate(vin):
        inputs += bytes.fromhex(txin["txid"])[::-1]
        inputs += txin["vout"].to_bytes(4, 'little')
        if i == input_index:
            # Set real scriptPubKey for this input
            script = bytes.fromhex(script_pubkey_hex)
            inputs += len(script).to_bytes(1, 'little') + script
        else:
            inputs += b'\x00'  # empty script
        inputs += txin["sequence"].to_bytes(4, 'little')

    output_count = len(vout).to_bytes(1, 'little')
    outputs = b''
    for txout in vout:
        value = int(txout["value"])
        script_bytes = bytes.fromhex(txout["scriptPubKey"]["hex"])
        outputs += value.to_bytes(8, 'little')
        outputs += len(script_bytes).to_bytes(1, 'little') + script_bytes

    locktime_bytes = locktime.to_bytes(4, 'little')

    base_tx = version + input_count + inputs + output_count + outputs + locktime_bytes + b'\x01\x00\x00\x00'  # SIGHASH_ALL
    return hashlib.sha256(hashlib.sha256(base_tx).digest()).digest()

from ecdsa import SigningKey, SECP256k1
from ecdsa.util import sigencode_der, number_to_string

def sigencode_der_canonize(r, s, order):
    """Ensure low-S canonical form for DER signature encoding."""
    if s > order // 2:
        s = order - s
    return sigencode_der(r, s, order)

def sign_input(private_key_hex: str, sighash: bytes) -> str:
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = sk.sign_digest_deterministic(
        sighash,
        sigencode=sigencode_der_canonize
    )
    return (signature + b'\x01').hex()  # Append SIGHASH_ALL

def wallet_file_path(name: str) -> str:
    return os.path.join(WALLET_DIR, f"{name}.json")







""" Im gonna refactor how we save wallets to disk 

    Im thinking we store maps of addresses, friendly names, and paths to the wallet file.
    
    maybe like this:

    {
        "name": "wallet_name",
        "created_at": "date_created",
        "extended_public_key": "xpub",
        "extended_private_key": "xprv",
        "HD_seed": "seed",
        "mnemonic": "mnemonic",
        "mnemonic_passphrase": "passphrase",
        "addresses": {
            "address":{
                "public_key": "address",
            "private_key": "address",
            "path": "address",
            "friendly_name": "address"
            },
            "friendly_name": "address",
            "path": "address"
        }
    }
    

"""



import typer
def import_wallet(path: str):
    """Import a wallet from a backup file."""
    try:
        with open(os.path.expanduser(path), "r") as f:
            data = json.load(f)
    except Exception as e:
        typer.echo(f"❌ Failed to read backup file: {e}")
        raise typer.Exit()

    mnemonic = data.get("mnemonic")
    passphrase = data.get("passphrase", "")
    wallet_name = typer.prompt("📝 Name this imported wallet")

    try:
        hdwallet = create_wallet(mnemonic, passphrase)
    except Exception as e:
        typer.echo(f"❌ Failed to reconstruct HD wallet: {e}")
        raise typer.Exit()

    addresses = []
    for i in range(len(data.get("addresses", []))):
        derivation = BIP44Derivation(coin_type=175, account=0, change=0, address=i)
        hdwallet.update_derivation(derivation)
        addresses.append({
            "index": i,
            "path": f"m/44'/175'/0'/0/{i}",
            "address": hdwallet.address(),
            "public_key": hdwallet.public_key(),
            "private_key": hdwallet.private_key(),
        })
        hdwallet.clean_derivation()

    hdwallet.name = wallet_name
    hdwallet.created_at = data.get("created_at", datetime.utcnow().isoformat())
    hdwallet.first_address = addresses[0]["address"] if addresses else ""
    hdwallet.addresses = addresses

    save_wallet(wallet_name, hdwallet)
    typer.echo(f"✅ Wallet '{wallet_name}' imported successfully.")
