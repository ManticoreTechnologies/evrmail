from .send_evr import send_evr_app
import typer
send_app = typer.Typer(name="send", help="🚀 Send EVR, assets, or metadata messages")
send_app.add_typer(send_evr_app)
__all__ = ["send_app"]