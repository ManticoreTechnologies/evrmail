from evrmail.utils.ipfs import is_ipfs_installed, is_ipfs_initialized, is_ipfs_running, install_ipfs, stop_ipfs_daemon, start_ipfs_daemon
from evrmail.config import IPFS_BINARY_PATH, IPFS_DIR
import subprocess
import shutil
import typer
import time
import os
from evrmail.utils.ipfs import add_to_ipfs

ipfs_app = typer.Typer(name="ipfs", help="Manage ipfs install and operation")

@ipfs_app.command("add")
def add(path: str):
    """Add a file to IPFS."""
    subprocess.run(["ipfs", "add", path])

@ipfs_app.command("start")
def start():
    """Ensure IPFS is set up and running."""

    if is_ipfs_running():
        print("IPFS is already running.")
    if not is_ipfs_installed():
        print("IPFS is not installed. Installing...")
        install_ipfs()
    elif not is_ipfs_initialized():
        print("IPFS is not initialized. Initializing...")
        subprocess.run(["ipfs", "init"], check=True)
    elif not is_ipfs_running():
        print("IPFS is not running. Starting...")
        start_ipfs_daemon()
        print("IPFS daemon started.")

@ipfs_app.command("install")
def install():
    """Install IPFS."""
    if is_ipfs_installed():
        print("IPFS is already installed.")
        return
    install_ipfs()

@ipfs_app.command("stop")
def stop():
    """Stop the IPFS daemon."""
    stop_ipfs_daemon()

@ipfs_app.command("restart")
def restart():
    """Restart the IPFS daemon."""
    stop_ipfs_daemon()
    time.sleep(2)
    start_ipfs_daemon()

@ipfs_app.command("reinstall")
def reinstall():
    """Reinstall IPFS."""
    stop_ipfs_daemon()
    install_ipfs()

@ipfs_app.command("uninstall")
def uninstall():
    """Uninstall IPFS."""
    stop_ipfs_daemon()
    try:
        subprocess.run(["sudo", "rm", IPFS_BINARY_PATH], check=True)
        print("IPFS binary removed.")
    except subprocess.CalledProcessError:
        print("Failed to remove IPFS binary.")
    if os.path.exists(IPFS_DIR):
        shutil.rmtree(IPFS_DIR)
        print("IPFS config directory removed.")

@ipfs_app.command("add")
def ipfs_add(filepath: str):
    """Add a file to IPFS and return the CID."""
    cid = add_to_ipfs(filepath)
    print(cid)
