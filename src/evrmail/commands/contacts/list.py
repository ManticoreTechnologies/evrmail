import typer
list_app = typer.Typer()


@list_app.command('list', help="🔍 List all contacts")
def list():
    from evrmail.config import load_config
    config = load_config()
    contacts = config.get('contacts')
    print(contacts)