""" evrmail.cli

Typer cli module.

evrmail send    |   Send a message
evrmail inbox   |   View your messages
evrmail wallet  |   Manage keys and funds
evrmail address |   Manage address book
evrmail config  |   View/set config like outbox, defaul addr
evrmail tx      |   Inspect or decode transactions
evrmail debug   |   Advanced dev tools

"""

import typer 
from .commands import send_app, inbox_app, wallets_app, addresses_app, config_app, tx_app, debug_app, outbox_app, balance_app, dev_app

# Main app
app = typer.Typer(
    name="evrmail",
    help="""
📬 EvrMail - Decentralized Email on Evrmore

A secure, blockchain-native messaging system powered by asset channels and encrypted metadata.
""",
    add_completion=False,
)

#app.add_typer(inbox_app)
app.add_typer(wallets_app)
app.add_typer(addresses_app)
app.add_typer(balance_app)
app.add_typer(send_app)
app.add_typer(dev_app)

#app.add_typer(config_app)
#app.add_typer(tx_app)
#app.add_typer(debug_app)
#app.add_typer(outbox_app)






#""" 📡 Clear Net Commands """
#clearnet_app = typer.Typer(help="📡 Commands for sending/receiving with the normal internet (SMTP, WebSocket)")
#from .commands import clearnet
## evrmail clearnet send <email> <message> 
#clearnet_app.add_typer(clearnet.send_app)
## evrmail clearnet buy-subasset <
#clearnet_app.add_typer(clearnet.buy_subasset_app)
## evrmail clearnet ??????
#
#""" Blockchain Commands """
#blockchain_app = typer.Typer()
#from .commands import blockchain
## evrmail blockchain send <address> <message>
#blockchain_app.add_typer(blockchain.send_app, help="")
## evrmail blockchain outbox {set,get} <asset_name>
#blockchain_app.add_typer(blockchain.outbox_app, help="Manage the asset from which to send messages.")
## evrmail blockchain addresses {add,remove,list} <address> <friendly_name>
#blockchain_app.add_typer(blockchain.addresses_app, name="addresses", help="Manage saved addresses")
#blockchain_app.add_typer(blockchain.contacts_app, name="contacts", help="Add a contact to send to, requires their public key.")
#
#
#
#
#app = typer.Typer(add_completion=False)
#app.add_typer(clearnet_app, name="clearnet", help="📡 Clear Net Commands")
#app.add_typer(blockchain_app, name="blockchain", help="⛓️  Blockchain Commands")
#from evrmail.commands.server import server_app
#app.add_typer(server_app, name="server", help="Run a mail bridge on your domain")
#
##contacts_app = typer.Typer()
##app.add_typer(contacts_app, name="contacts")
##import evrmail.commands.compose
#import evrmail.commands.ipfs
#app.add_typer(evrmail.commands.ipfs.ipfs_app, name="ipfs")
##import evrmail.commands.drafts
##app.add_typer(evrmail.commands.drafts.drafts_app, name="drafts")
#import evrmail.commands.inbox
#app.add_typer(evrmail.commands.inbox.inbox_app, name="inbox")
#import evrmail.commands.daemon
#app.add_typer(evrmail.commands.daemon.daemon_app, name="daemon")
#import evrmail.commands.wallet
#app.add_typer(evrmail.commands.wallet.wallet_app)
##import evrmail.commands.smtp
##app.add_typer(evrmail.commands.smtp.smtp_app, name="smtp")
##import evrmail.commands.frp
##app.add_typer(evrmail.commands.frp.frp_app, name="frp")
##import evrmail.commands.register
##app.add_typer(evrmail.commands.register.register_app, name="register")
##import evrmail.commands.forward
##app.add_typer(evrmail.commands.forward.forward_app, name="forward")
##
##
#
#
#
def main():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()