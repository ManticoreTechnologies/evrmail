import typer
from .list import list_app
from .unread import unread_app
from .open import open_app
from .filter import filter_app
from .mark_read import mark_read_app
from .delete import delete_app

inbox_app = typer.Typer(name="inbox", help="View your messages")

inbox_app.add_typer(list_app)
inbox_app.add_typer(unread_app)
inbox_app.add_typer(open_app)
inbox_app.add_typer(filter_app)
inbox_app.add_typer(mark_read_app)
inbox_app.add_typer(delete_app)


__all__=["inbox_app"]