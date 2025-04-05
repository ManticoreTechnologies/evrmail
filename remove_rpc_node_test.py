import requests
from requests.auth import HTTPBasicAuth

# === CONFIG ===
EVRMORE_RPC_HOST = "77.90.40.55"
EVRMORE_RPC_PORT = 8819
RPC_USER = "evruser"
RPC_PASSWORD = "changeThisToAStrongPassword123"

def send_rpc(method, params=[]):
    url = f"http://{EVRMORE_RPC_HOST}:{EVRMORE_RPC_PORT}/"
    payload = {
        "jsonrpc": "1.0",
        "id": "auth_test",
        "method": method,
        "params": params
    }

    try:
        response = requests.post(url, json=payload, auth=HTTPBasicAuth(RPC_USER, RPC_PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"RPC Error: {e}"

# === Example Usage ===
if __name__ == "__main__":
    result = send_rpc("getblockchaininfo")
    print(result)
