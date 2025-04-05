"""
evrmail/inbox/open.py

Launch interactive inbox UI (arrow nav etc.)

Usage:
evrmail inbox open

"""

import typer

open_app = typer.Typer()

@open_app.command(help="Launch interactive inbox UI (arrow nav etc.)")
def open():
    print("To be implemented")
