# evrmail/cli.py

import typer
from evrmore_rpc import EvrmoreClient
import subprocess
import os
import hashlib
from evrmail.config import load_config, save_config
import base58
app = typer.Typer()
contacts_app = typer.Typer()
app.add_typer(contacts_app, name="contacts")
from evrmail.commands.outbox import outbox_app
app.add_typer(outbox_app, name="outbox")
import evrmail.commands.compose
import evrmail.commands.ipfs
app.add_typer(evrmail.commands.ipfs.ipfs_app, name="ipfs")
import evrmail.commands.drafts
app.add_typer(evrmail.commands.drafts.drafts_app, name="drafts")
import evrmail.commands.inbox
app.add_typer(evrmail.commands.inbox.inbox_app, name="inbox")
import evrmail.commands.daemon
app.add_typer(evrmail.commands.daemon.daemon_app, name="daemon")
