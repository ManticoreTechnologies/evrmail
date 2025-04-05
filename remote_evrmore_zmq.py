from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.zmq import ZMQTopic
import time
EVRMORE_RPC_HOST = "tcp://77.90.40.55"
EVRMORE_RPC_PORT = 8819
RPC_USER = "evruser"
RPC_PASSWORD = "changeThisToAStrongPassword123"
rpc_client = EvrmoreClient(url="tcp://77.90.40.55", rpcuser="evruser", rpcpassword="changeThisToAStrongPassword123", rpcport=8819)
zmq_client = EvrmoreZMQClient(zmq_host="77.90.40.55", zmq_port=28332, rpc_client=rpc_client, auto_decode=True, auto_create_rpc=False)
@zmq_client.on(ZMQTopic.TX)
def on_tx(tx):
    print(tx)
zmq_client.start()
print("✅ Daemon is now listening for messages.")
try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\n🛑 Stopping evrmail Daemon...")
finally:
    zmq_client.stop_sync()