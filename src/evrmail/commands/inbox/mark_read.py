"""
evrmail/inbox/mark_read.py

Mark message as read

Usage:
evrmail inbox mark_read

"""

import typer

mark_read_app = typer.Typer()

@mark_read_app.command(help="Mark message as read")
def mark_read():
    print("To be implemented")
