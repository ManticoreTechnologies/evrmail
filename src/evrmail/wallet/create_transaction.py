""" Create a raw Evrmore transaction """

from evrmore_rpc import EvrmoreClient
from evrmail.wallet import get_all_addresses  # You should implement this helper if not already
from evrmail.config import load_config

rpc = EvrmoreClient()

def create_transaction(to_address: str, cid: str, outbox_asset: str, change_address: str):
    """
    Create a raw transaction to send a message via a transfer_asset on the Evrmore blockchain.

    Args:
        to_address (str): The recipient's blockchain address.
        cid (str): The IPFS CID containing the message batch.
        outbox_asset (str): The asset name used to send the message.
        change_address (str): Your change output address for coin UTXOs.
    """

    # 1. Load all wallet addresses
    wallet_addresses = get_all_wallet_addresses()  # Should return List[str]

    # 2. Fetch all UTXOs from those addresses
    utxos = rpc.getaddressutxos({"addresses": wallet_addresses})

    # 3. Select asset UTXO for message
    asset_input = next(
        (u for u in utxos if u.get("assetName") == outbox_asset),
        None
    )
    if not asset_input:
        raise Exception(f"No spendable asset UTXO found for {outbox_asset}")

    # 4. Select a coin UTXO to cover fee
    coin_input = next(
        (u for u in utxos if "assetName" not in u and u["satoshis"] > 1000),
        None
    )
    if not coin_input:
        raise Exception("No coin UTXO available to pay transaction fees")

    # 5. Construct inputs
    inputs = [
        {"txid": asset_input["txid"], "vout": asset_input["outputIndex"]},
        {"txid": coin_input["txid"], "vout": coin_input["outputIndex"]},
    ]

    # 6. Construct outputs
    message_output = {
        to_address: {
            "transfer_asset": {
                "name": outbox_asset,
                "amount": 1,
                "message": cid,
            }
        }
    }

    # Estimate change after assuming a rough fee of 1000 satoshis
    change = coin_input["satoshis"] - 1000
    if change > 0:
        message_output[change_address] = change / 1e8

    # 7. Build raw transaction
    raw_tx = rpc.createrawtransaction(inputs, message_output)

    print("Raw transaction created:", raw_tx)
    return raw_tx
