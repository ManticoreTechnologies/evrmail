import typer
contacts_app = typer.Typer()

@contacts_app.command('add')
def add(address: str, pubkey: str, friendly_name: str = typer.Option(None, "--friendly-name", "-f", help="A friendly name for the address")):
    from evrmail.config import load_config, save_config
    config = load_config()
    if 'contacts' not in config:
        config['contacts'] = {}
    config['contacts'][address] = {"pubkey": pubkey, "friendly_name": friendly_name}
    save_config(config)

@contacts_app.command('remove')
def remove(address_or_name: str):
    from evrmail.config import load_config, save_config
    config = load_config()
    contact_to_delete = ""
    if 'contacts' not in config:
        config['contacts'] = {}
    for address in config['contacts']:
        data = config['contacts'].get(address)
        if address == address_or_name or data.get('friendly_name') == address_or_name:
            contact_to_delete = address
    del config['contacts'][contact_to_delete]
    print(f"Contact {address_or_name} removed.")
    save_config(config)

@contacts_app.command('list')
def list():
    from evrmail.config import load_config
    config = load_config()
    contacts = config.get('contacts')
    print(contacts)

