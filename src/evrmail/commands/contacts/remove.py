import typer
remove_app = typer.Typer()

@remove_app.command('remove', help="🗑️  Remove a contact")
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