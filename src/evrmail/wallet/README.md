
from evrmail import wallet

wallet.addresses 
wallet.tx
wallet.p2sh
wallet.pubkey
wallet.pubkeyhash
wallet.script

--- Addresses
wallet.addresses.get_all_addresses()
wallet.addresses.get_all_addresses_by_wallet()

--- Tx
wallet.tx.create_transaction()
wallet.tx.sign_transaction()
wallet.tx.send_transaction()

--- P2SH
