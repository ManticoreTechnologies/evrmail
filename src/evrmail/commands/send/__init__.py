from .send_evr import send_evr_app
from .send_asset import send_asset_app
from .send_msg import send_msg_app
import typer
send_app = typer.Typer(name="send", help="🚀 Send EVR, assets, or metadata messages")
send_app.add_typer(send_evr_app)
send_app.add_typer(send_asset_app)
send_app.add_typer(send_msg_app)
__all__ = ["send_app"]