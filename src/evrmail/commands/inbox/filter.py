"""
evrmail/inbox/filter.py

Show messages from a specific outbox

Usage:
evrmail inbox filter

"""

import typer

filter_app = typer.Typer()

@filter_app.command(help="Show messages from a specific outbox")
def filter():
    print("To be implemented")
