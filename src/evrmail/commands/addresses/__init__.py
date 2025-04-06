import typer
addresses_app=typer.Typer(name="addresses", help="🏷️  Manage addresses and keys")
__all__=["addresses_app"]

from .list import list_app
from .get import get_app
from .active import active_app
from .use import use_app
from .validate import validate_app
from .dumpprivkey import dumpprivkey_app
from .publickey import publickey_app

addresses_app.add_typer(list_app)
addresses_app.add_typer(get_app)
addresses_app.add_typer(active_app)
addresses_app.add_typer(use_app)
addresses_app.add_typer(validate_app)
addresses_app.add_typer(dumpprivkey_app)
addresses_app.add_typer(publickey_app)