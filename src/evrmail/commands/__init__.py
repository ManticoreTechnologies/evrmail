from evrmail.commands.frp import frp_app
from evrmail.commands.smtp import smtp_app
from evrmail.commands.daemon import daemon_app
from evrmail.commands.drafts import drafts_app
from evrmail.commands.ipfs import ipfs_app
from evrmail.commands.register import register_app

from .clearnet import send_app as clearnet_send_app
from .blockchain import send_app as blockchain_send_app

from .balance import balance_app
from .addresses import addresses_app
from .config import config_app
from .tx import tx_app
from .debug import debug_app
from .wallets import wallets_app
from .send import send_app
from .outbox import outbox_app
from .inbox import inbox_app
from .dev import dev_app
from .contacts import contacts_app