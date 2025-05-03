evrmail --help

evrmail outbox set <owned_asset>

evrmail outbox get

evrmail inbox open

evrmail inbox list

evrmail inbox unread

evrmail compose

evrmail daemon start

evrmail daemon stop

evrmail ipfs install

evrmail ipfs uninstall

evrmail ipfs start 

evrmail ipfs stop


Evrmail has multi-wallet support, wallets are stored in ~/.evrmail/wallets/
Create, Remove, Update, and Delete wallets using `evrmail wallets` subcommands

More info coming soon!



## Quick Setup!
`python3 -m venv .venv`
`source .venv/bin/activate`
`pip install evrmail`
`evrmail --help`


## Quick Start!
Create a wallet 
`evrmail wallets create`
Create an address
`evrmail receive MyInbox`
Get address data (Pubkey for contact exchange)
`evrmail addresses get MyInbox`
Copy your public key from the output and give it to your contacts.
`xoznir@xoznir:~/Documents/Manticore_Technologies/Python/evmail-dev$ evrmail addresses get MyInbox

📬 Address Info:

  🏷️  Friendly Name : MyInbox
  🔢 Index         : 1002
  🧭 Path          : m/44'/175'/0'/0/1002
  📬 Address       : EKinLJrSEUBpurTJkNo4XKnhK5X31g1Ag2
  🔓 Public Key    : 020e16bd4607693bdca2f18cce2d1a62d01b17156878f352c63ca7aede455858ae
  📦 Wallet        : wallet_fit_gospel_7545`

`evrmail contacts add EX3T4XZvp7SrjuKonp7daKCtQFCDpSoP64 035c5898fe7d9972ed602c04487e21c4a0574f4d9bcf653c0b425ce0b367fbf5aa --friendly-name "myfriend"`


Developer Notes:

1. Make sure you have cmake installed. 

sudo apt get update
sudo apt get install cmake

2. Make sure you have 

sudo apt install libxcb-cursor0

3. Make sure you make ~/.evrmail/config.json 

sudo nano ~/.evrmail/config.json
```
{
  "ipfs_path": "/home/xoznir/.ipfs",
  "ipfs_binary": "/usr/local/bin/ipfs",
  "addresses": {},
  "active_address": null,
  "aliases": {},
  "rpc_host": "tcp://77.90.40.55",
  "rpc_port": 8819,
  "rpc_user": "evruser",
  "rpc_password": "changeThisToAStrongPassword123",
  "contacts": {
    "EX3T4XZvp7SrjuKonp7daKCtQFCDpSoP64": {
      "pubkey": "035c5898fe7d9972ed602c04487e21c4a0574f4d9bcf653c0b425ce0b367fbf5aa",
      "friendly_name": "myfriend"
    }
  }
}
```

4. Install Pyside6 dependencies

sudo apt install libxcb-xinerama0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-render-util0 libxcb-image0 libxcb-util1

