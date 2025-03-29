from evrmail.commands.frp import frp_app
from evrmail.commands.smtp import smtp_app
from evrmail.commands.daemon import daemon_app
from evrmail.commands.inbox import inbox_app
from evrmail.commands.drafts import drafts_app
from evrmail.commands.ipfs import ipfs_app
from evrmail.commands.register import register_app
from evrmail.commands.clearnet.send import send_app

from .clearnet import send_app as clearnet_send_app
from .blockchain import send_app as blockchain_send_app

__all__ = ["clearnet_send_app", "blockchain_send_app"]