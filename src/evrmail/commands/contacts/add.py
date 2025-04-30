import typer
add_app = typer.Typer()

@add_app.command('add', help="👤 Add a contact")
def add(address: str, pubkey: str, friendly_name: str = typer.Option(None, "--friendly-name", "-f", help="A friendly name for the address")):
    from evrmail.config import load_config, save_config
    config = load_config()
    if 'contacts' not in config:
        config['contacts'] = {}
    config['contacts'][address] = {"pubkey": pubkey, "friendly_name": friendly_name}
    save_config(config)