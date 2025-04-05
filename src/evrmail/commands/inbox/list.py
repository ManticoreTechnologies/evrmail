"""
evrmail/inbox/list.py

Show all received messages (sorted newest-first)

Usage:
evrmail inbox list

"""

import typer

list_app = typer.Typer()

@list_app.command(help="Show all received messages (sorted newest-first)")
def list():
    print("To be implemented")
