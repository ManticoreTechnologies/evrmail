# evrmail/frp/client_manager.py
import os
import subprocess
import requests
from pathlib import Path
import typer

FRP_CLIENT_BINARY = Path.home() / ".evrmail" / "frpc"
FRP_CONFIG_FILE = Path.home() / ".evrmail" / "frpc.toml"
DOMAIN_API = "http://api.evrmail.com/register"

frp_app = typer.Typer()

@frp_app.command("start")
def start():
    """Start the FRP client with the current configuration."""
    if not FRP_CLIENT_BINARY.exists():
        typer.echo("❌ FRPC binary not found. Run `evrmail frp install` first.")
        raise typer.Exit(1)
    typer.echo("🚀 Starting FRPC...")
    subprocess.Popen([str(FRP_CLIENT_BINARY), "-c", str(FRP_CONFIG_FILE)])

@frp_app.command("stop")
def stop():
    """Stop all running FRPC processes."""
    typer.echo("🛑 Stopping FRPC...")
    subprocess.run(["pkill", "-f", "frpc"], check=False)

@frp_app.command("restart")
def restart():
    """Restart FRPC."""
    stop()
    start()

@frp_app.command("status")
def status():
    """Check if FRPC is running."""
    result = subprocess.run(["pgrep", "-f", "frpc"], capture_output=True, text=True)
    if result.returncode == 0:
        typer.echo("✅ FRPC is running.")
    else:
        typer.echo("❌ FRPC is not running.")

@frp_app.command("install")
def install():
    """Download and install FRPC binary to ~/.evrmail/frpc."""
    typer.echo("⬇️  Downloading FRPC...")
    os.makedirs(FRP_CLIENT_BINARY.parent, exist_ok=True)
    url = "https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz"
    archive_path = FRP_CLIENT_BINARY.parent / "frp.tar.gz"
    subprocess.run(["curl", "-L", "-o", str(archive_path), url], check=True)
    subprocess.run(["tar", "-xzf", str(archive_path), "-C", str(FRP_CLIENT_BINARY.parent)], check=True)
    frpc_extracted = FRP_CLIENT_BINARY.parent / "frp_0.52.3_linux_amd64" / "frpc"
    frpc_extracted.rename(FRP_CLIENT_BINARY)
    FRP_CLIENT_BINARY.chmod(0o755)
    typer.echo("✅ FRPC installed.")

@frp_app.command("config")
def config():
    """Print path to current FRPC config."""
    typer.echo(f"📝 Config file: {FRP_CONFIG_FILE}")

@frp_app.command("set-domain")
def set_domain(domain: str):
    """Register the domain and configure FRPC."""
    typer.echo(f"🌐 Setting domain to: {domain}")
    typer.echo("📡 Contacting EvrMail domain API...")
    try:
        res = requests.post(DOMAIN_API, json={"domain": domain})
        res.raise_for_status()
        data = res.json()
        typer.echo(f"✅ Domain registered with remote port {data['port']}")

        typer.echo("📋 Now add the following DNS records at your DNS provider:")
        typer.echo(f"  📌 A Record: smtp.{domain} → vpn.evrmail.com")
        typer.echo(f"  📌 MX Record: @ → smtp.{domain} (priority 10)")
        typer.echo("⚠️  It may take some time for DNS changes to propagate.")

        config = f"""
serverAddr = "vpn.evrmail.com"
serverPort = 7000

token = "mysecretkey"

[log]
level = "info"

[[proxies]]
name = "{domain}-smtp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 2525
remotePort = {data['port']}
"""
        with open(FRP_CONFIG_FILE, "w") as f:
            f.write(config)
        typer.echo("✅ Local FRPC configuration written.")
        typer.echo("🚀 Run `evrmail frp restart` to apply the changes.")
    except requests.RequestException as e:
        typer.echo(f"❌ Failed to register domain: {e}")
