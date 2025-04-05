from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Evrmore
from hdwallet.mnemonics.bip39 import BIP39Mnemonic
import requests
import time
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
seed = mnemo.generate()

# === Generate 24-word mnemonic and derive HD wallet ===
_mnemonic = BIP39Mnemonic(mnemonic=seed)
print(seed)

# Create HD wallet for Evrmore
hdwallet = HDWallet(cryptocurrency=Evrmore)
hdwallet.from_mnemonic(_mnemonic)

# Extract info
address = hdwallet.address()
xpub = hdwallet.xpublic_key()
xprv = hdwallet.xprivate_key()
wif = hdwallet.wif()

print("Address:", address)
print("xpub:", xpub)
print("xprv:", xprv)
print("WIF:", wif)