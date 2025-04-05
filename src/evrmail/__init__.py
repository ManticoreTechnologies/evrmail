from .cli import app
from .config import load_config
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient


evrmail_config = load_config()

rpc_client = EvrmoreClient(url=evrmail_config.get('rpc_host'), rpcuser=evrmail_config.get('rpc_user'), rpcpassword=evrmail_config.get('rpc_password'), rpcport=evrmail_config.get('rpc_port'))
zmq_client = EvrmoreZMQClient(zmq_host="77.90.40.55", zmq_port=28332, rpc_client=rpc_client, auto_decode=True, auto_create_rpc=False)

__all__ = ["evrmail_config", "rpc_client", "zmq_client"]

def main():
    app()

if __name__ == "__main__":
    main()
