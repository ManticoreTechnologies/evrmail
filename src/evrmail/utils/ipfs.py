import shutil
import os
import subprocess
from evrmail.config import IPFS_DIR, IPFS_BINARY_PATH
import time
import platform
import sys
import getpass
import tarfile
import urllib.request
import requests
import base64
import json

# evrmail/utils/ipfs.py

def fetch_ipfs_text(cid: str) -> str:
    try:
        # 🚀 Using public IPFS gateway
        url = f"https://ipfs.io/ipfs/{cid}"
        response = requests.get(url)
        if response.ok:
            return response.text
        else:
            return None
    except Exception as e:
        print(f"⚠️ IPFS fetch failed: {e}")
        return None

def fetch_ipfs_resource(hash_or_path, use_ipns=False, timeout=10):
    """
    Fetch a resource from IPFS or IPNS.
    
    Args:
        hash_or_path (str): The IPFS hash or IPNS path to fetch
        use_ipns (bool): True if the hash is an IPNS name, False for IPFS hash
        timeout (int): Request timeout in seconds
        
    Returns:
        tuple: (content_type, content) or (None, None) if fetch fails
    """
    import requests
    import logging
    from time import sleep
    
    # Don't process empty hashes
    if not hash_or_path or hash_or_path.strip() == '':
        logging.error("Empty IPFS/IPNS hash provided")
        return None, None
    
    # Clean up the hash (remove ipfs:// or ipns:// if present)
    hash_or_path = hash_or_path.strip()
    hash_or_path = hash_or_path.replace('ipfs://', '').replace('ipns://', '')
    
    # Determine the gateway URL
    gateway_type = 'ipns' if use_ipns else 'ipfs'
    base_url = f"https://ipfs.io/{gateway_type}/{hash_or_path}"
    
    logging.info(f"Fetching {'IPNS' if use_ipns else 'IPFS'} resource: {base_url}")
    
    # Try multiple times with exponential backoff
    max_retries = 3
    retry_delay = 1  # starting delay in seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, timeout=timeout)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'text/html')
                return content_type, response.text
            
            # If the resource is not found or gateway error
            if response.status_code in [404, 504, 502]:
                logging.warning(f"IPFS resource not found or gateway error: {base_url} (status: {response.status_code})")
                
                # Try an alternative gateway if first attempt failed
                if attempt == 0:
                    alt_gateways = [
                        f"https://ipfs.io/{gateway_type}/{hash_or_path}",
                        f"https://cloudflare-ipfs.com/{gateway_type}/{hash_or_path}",
                        f"https://dweb.link/{gateway_type}/{hash_or_path}"
                    ]
                    
                    for alt_url in alt_gateways:
                        logging.info(f"Trying alternative gateway: {alt_url}")
                        try:
                            alt_response = requests.get(alt_url, timeout=timeout)
                            if alt_response.status_code == 200:
                                content_type = alt_response.headers.get('Content-Type', 'text/html')
                                return content_type, alt_response.text
                        except Exception as e:
                            logging.warning(f"Alternative gateway failed: {alt_url} - {str(e)}")
                            continue
            
            # For other errors, retry with backoff
            logging.warning(f"IPFS fetch failed (attempt {attempt+1}/{max_retries}): {response.status_code}")
            
        except requests.RequestException as e:
            logging.warning(f"IPFS request error (attempt {attempt+1}/{max_retries}): {str(e)}")
        
        # Sleep with exponential backoff before retrying
        if attempt < max_retries - 1:
            sleep_time = retry_delay * (2 ** attempt)
            logging.info(f"Retrying in {sleep_time} seconds...")
            sleep(sleep_time)
    
    logging.error(f"Failed to fetch {'IPNS' if use_ipns else 'IPFS'} resource after {max_retries} attempts: {hash_or_path}")
    return None, None

def fetch_ipns_resource(key: str) -> (str, str):
    """
    Fetch IPFS content. Returns (mime_type, data).
    """
    try:
        url = f"https://ipfs.io/ipns/{key}"
        response = requests.get(url)

        if not response.ok:
            return None, None

        content_type = response.headers.get("Content-Type", "")
        return content_type, response.content  # return raw bytes
    except Exception as e:
        print(f"⚠️ IPNS fetch failed: {e}")
        return None, None
    
def is_ipfs_installed():
    return shutil.which("ipfs") is not None

def is_ipfs_initialized():
    return os.path.exists(os.path.join(IPFS_DIR, "config"))

def is_ipfs_running(port=5101):
    try:
        res = requests.post(f"http://127.0.0.1:{port}/api/v0/id", timeout=3)
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_ipfs_daemon(api_port=5101, gateway_port=9090):
    print(f"Starting IPFS daemon on API port {api_port}, Gateway port {gateway_port}...")

    # First, make sure IPFS is initialized
    subprocess.run(["ipfs", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Update config with new API and Gateway addresses
    subprocess.run(["ipfs", "config", "Addresses.API", f"/ip4/127.0.0.1/tcp/{api_port}"])
    subprocess.run(["ipfs", "config", "Addresses.Gateway", f"/ip4/127.0.0.1/tcp/{gateway_port}"])

    subprocess.Popen(["ipfs", "daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    print("✅ IPFS daemon started.")

def stop_ipfs_daemon(port=5101):
    try:
        res = requests.post(f"http://127.0.0.1:{port}/api/v0/shutdown", timeout=3)
        if res.ok:
            print("✅ IPFS daemon shutting down via API.")
        else:
            print(f"⚠️ IPFS responded with code {res.status_code}: {res.text}")
    except requests.exceptions.RequestException:
        print("❌ Failed to contact IPFS daemon or it's already stopped.")

def ensure_ipfs():
    if not is_ipfs_installed():
        install_ipfs()
    if not is_ipfs_initialized():
        subprocess.run(["ipfs", "init"], check=True)
    if not is_ipfs_running():
        start_ipfs_daemon()

def install_ipfs():
    system = platform.system().lower()
    arch = platform.machine()
    version = "v0.24.0"
    base_url = "https://dist.ipfs.tech/kubo/"

    if system == "linux" and arch == "x86_64":
        url = f"{base_url}{version}/kubo_{version}_linux-amd64.tar.gz"
    elif system == "darwin" and arch == "x86_64":
        url = f"{base_url}{version}/kubo_{version}_darwin-amd64.tar.gz"
    else:
        print("Unsupported OS/architecture. Please install IPFS manually.")
        sys.exit(1)

    tmp_dir = f"/tmp/evrmail-ipfs-{int(time.time())}"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_tar = os.path.join(tmp_dir, "ipfs.tar.gz")

    try:
        print(f"Downloading IPFS from {url}...")
        urllib.request.urlretrieve(url, tmp_tar)
    except PermissionError:
        print("Permission denied writing to /tmp. Please rerun with sudo.")
        sys.exit(1)

    with tarfile.open(tmp_tar) as tar:
        tar.extractall(path=tmp_dir)
        extracted_dirs = list({name.split("/")[0] for name in tar.getnames()})

    if not extracted_dirs:
        print("Failed to locate extracted IPFS directory. Please check the archive format.")
        sys.exit(1)

    ipfs_path = os.path.join(tmp_dir, extracted_dirs[0], "ipfs")
    if not os.path.exists(ipfs_path):
        print(f"IPFS binary not found at {ipfs_path}. Aborting.")
        sys.exit(1)

    try:
        shutil.copy(ipfs_path, IPFS_BINARY_PATH)
        os.chmod(IPFS_BINARY_PATH, 0o755)
        print("IPFS installed to /usr/local/bin/ipfs")
    except PermissionError:
        print("Permission denied. Attempting to run sudo to install IPFS...")
        sudo_pw = getpass.getpass("Enter your sudo password: ")
        install_script = f"echo {sudo_pw} | sudo -S cp {ipfs_path} {IPFS_BINARY_PATH} && echo {sudo_pw} | sudo -S chmod 755 {IPFS_BINARY_PATH}"
        result = subprocess.run(install_script, shell=True)
        if result.returncode != 0:
            print("Failed to install IPFS with sudo. Please try manually.")
            sys.exit(1)
        print("IPFS installed using sudo.")

    if not is_ipfs_initialized():
        try:
            subprocess.run([IPFS_BINARY_PATH, "init"], check=True)
            print("IPFS initialized.")
        except subprocess.CalledProcessError:
            print("IPFS already initialized or failed to initialize.")

    start_ipfs_daemon()

def add_to_ipfs(batch_payload: dict):
    """Add a file to IPFS and return the CID."""
    payload_path = f"/tmp/evrmail-ipfs-{int(time.time())}.json"
    with open(payload_path, "w") as f:
        f.write(json.dumps(batch_payload))
    try:
        result = subprocess.run(["ipfs", "add", "-q", payload_path], capture_output=True, text=True, check=True)
        cid = result.stdout.strip()
        os.remove(payload_path)
        return cid
    except subprocess.CalledProcessError as e:
        print(f"Failed to add file to IPFS: {e}")

def fetch_ipfs_json(cid: str, port: int = 5101) -> dict:
    """Fetch a JSON object from IPFS, using local node first and falling back to public gateway."""
    local_url = f"http://127.0.0.1:{port}/api/v0/cat?arg={cid}"
    public_url = f"https://ipfs.io/ipfs/{cid}"

    # Try local IPFS node first
    try:
        response = requests.post(local_url, timeout=5)
        response.raise_for_status()
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Local IPFS node failed: {e}")
    except json.JSONDecodeError:
        print("❌ Local IPFS returned invalid JSON.")

    # Fallback to public gateway
    try:
        response = requests.get(public_url, timeout=10)
        response.raise_for_status()
        print("🌐 Fetched from public IPFS gateway.")
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"❌ Public IPFS fetch failed: {e}")
    except json.JSONDecodeError:
        print("❌ Public IPFS returned invalid JSON.")

    return {}

