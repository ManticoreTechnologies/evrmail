"""
evrmail/inbox/unread.py

List only unread messages

Usage:
evrmail inbox unread

"""

import typer

unread_app = typer.Typer()

@unread_app.command(help="List only unread messages")
def unread():
    print("To be implemented")
