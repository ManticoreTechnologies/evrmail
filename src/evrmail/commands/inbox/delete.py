"""
evrmail/inbox/delete.py

Delete a local copy of message

Usage:
evrmail inbox delete

"""

import typer

delete_app = typer.Typer()

@delete_app.command(help="Delete a local copy of message")
def delete():
    print("To be implemented")
