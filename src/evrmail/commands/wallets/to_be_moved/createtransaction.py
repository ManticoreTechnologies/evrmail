import typer
from evrmail.config import load_config
from evrmore_rpc import EvrmoreClient
import typer

createtransaction_app = typer.Typer()

evrmail_config = load_config()

""" You can now use a public node! Using simply rpc_client=EVrmoreClient() will use your local evrmore node! """
EVRMORE_RPC_HOST = "tcp://77.90.40.55"
EVRMORE_RPC_PORT = 8819
RPC_USER = "evruser"
RPC_PASSWORD = "changeThisToAStrongPassword123"
rpc_client = EvrmoreClient()#EvrmoreClient(url="tcp://77.90.40.55", rpcuser="evruser", rpcpassword="changeThisToAStrongPassword123", rpcport=8819)
wallet_app = typer.Typer(name="wallet", help="Manage your Evrmore wallets")

@createtransaction_app.command("createtransaction", help="💰 Create a transaction")
def createtransaction():
    from evrmail.wallet.tx.create.transfer_asset import create_transfer_asset_transaction
    from evrmail.wallet.tx.create.send_evr import create_send_evr_transaction
    #tx = create_transfer_asset_transaction("EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH", "EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH", "HANDLE!", 100000000, "QmYGT3dmWLnUZWYDTTxVyf7pBDQztq1DhvsHA4biEzwbYL")
    tx = create_send_evr_transaction("EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH", "EHKUYgMKn91u8UXdXuZ1SATXd5qE72edNH", 1000)
    typer.echo(tx)