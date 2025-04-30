import typer
contacts_app=typer.Typer(name="contacts",help="📱 Manage contacts")
__all__=["contacts_app"]

from .add import add_app
contacts_app.add_typer(add_app)

from .remove import remove_app
contacts_app.add_typer(remove_app)

from .list import list_app
contacts_app.add_typer(list_app)