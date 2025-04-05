import base58
import hashlib
from ecdsa import SigningKey, SECP256k1, util

# Decode WIF
def wif_to_privkey(wif):
    decoded = base58.b58decode_check(wif)
    if decoded[0] != 0x80:
        raise ValueError("Invalid WIF prefix")
    return decoded[1:33]

def compress_pubkey(vk):
    x = vk.to_string()[:32]
    y = vk.to_string()[32:]
    return (b'\x02' if int.from_bytes(y, 'big') % 2 == 0 else b'\x03') + x

def sha256(data):
    return hashlib.sha256(data).digest()

def hash256(data):
    return sha256(sha256(data))

def serialize_tx_for_sig(tx, input_index, script_pubkey_hex):
    version = tx['version'].to_bytes(4, 'little')
    locktime = tx['locktime'].to_bytes(4, 'little')
    hash_type = (1).to_bytes(4, 'little')  # SIGHASH_ALL

    def serialize_input(vin, script_override_hex=None):
        out = bytes.fromhex(vin['txid'])[::-1]
        out += vin['vout'].to_bytes(4, 'little')
        if script_override_hex is not None:
            script = bytes.fromhex(script_override_hex)
            out += len(script).to_bytes(1, 'little') + script
        else:
            out += b'\x00'
        out += vin['sequence'].to_bytes(4, 'little')
        return out

    def serialize_output(vout):
        value = int(vout['value'] * 1e8)
        out = value.to_bytes(8, 'little')
        spk = bytes.fromhex(vout['scriptPubKey']['hex'])
        out += len(spk).to_bytes(1, 'little') + spk
        return out

    inputs = b''.join(
        serialize_input(vin, script_pubkey_hex if i == input_index else None)
        for i, vin in enumerate(tx['vin'])
    )
    outputs = b''.join(serialize_output(vout) for vout in tx['vout'])

    return (
        version +
        len(tx['vin']).to_bytes(1, 'little') +
        inputs +
        len(tx['vout']).to_bytes(1, 'little') +
        outputs +
        locktime +
        hash_type
    )

# Inputs
wif1 = "KzL6Hx32V8rxUqbHAua1hsMYt375ZdWdmUxBaCvtKBq5oxJ4tGnw"
wif2 = "L1yy46sgpEKqJUUeErRgJDkEFqMYW2ah9Zhc2EoDp9SDjSv1oe1J"

priv1 = wif_to_privkey(wif1)
priv2 = wif_to_privkey(wif2)
sk1 = SigningKey.from_string(priv1, curve=SECP256k1)
sk2 = SigningKey.from_string(priv2, curve=SECP256k1)
pub1 = compress_pubkey(sk1.get_verifying_key())
pub2 = compress_pubkey(sk2.get_verifying_key())

confirmed_tx = {
    "version": 2,
    "locktime": 1263107,
    "vin": [
        {
            "txid": "12a84977df2df2004e16c8ee694ad0ea14d7c987cc6ce3b9697350bfd56bb17d",
            "vout": 1,
            "scriptSig": {"asm": "", "hex": ""},
            "sequence": 4294967294
        },
        {
            "txid": "c860df21811641e38809e0ac55321923fc881a0a0a26e6331ea21c99ac2714e1",
            "vout": 2,
            "scriptSig": {"asm": "", "hex": ""},
            "sequence": 4294967294
        }
    ],
    "vout": [
        {
            "value": 0.48686118,
            "scriptPubKey": {
                "hex": "76a914b21fc4ae7a3b615148229cd266cce01cdc1d007e88ac"
            }
        },
        {
            "value": 0.0,
            "scriptPubKey": {
                "hex": "76a91401cf55d09a3130bff0618afa8a125d959d81a96e88acc014657672740748414e444c452100e1f5050000000075"
            }
        }
    ]
}

# Prev scriptPubKeys
script_pubkey_hex1 = "76a9149731c2d044a7ced52b1a6ac0a3ab03a01d3a213e88ac"
script_pubkey_hex2 = "76a9144a06be9e0bcb97b66cbb740dafb5648e22b6b81c88acc00c6576726f0748414e444c452175"

# Sign each input
for i, (sk, pubkey, script_hex) in enumerate([
    (sk1, pub1, script_pubkey_hex1),
    (sk2, pub2, script_pubkey_hex2)
]):
    preimage = serialize_tx_for_sig(confirmed_tx, i, script_hex)
    sighash = hash256(preimage)
    sig = sk.sign_digest_deterministic(sighash, sigencode=util.sigencode_der) + b'\x01'
    scriptSig = (
        len(sig).to_bytes(1, 'little') + sig +
        len(pubkey).to_bytes(1, 'little') + pubkey
    )
    confirmed_tx['vin'][i]['scriptSig']['hex'] = scriptSig.hex()

# Show result
import json
print(json.dumps(confirmed_tx, indent=2))
