# EvrMail

A secure, blockchain-native email application built on the Evrmore blockchain.

## 🔄 UI Framework Migration

This project was migrated from PySide6 (Qt) to Flet (Flutter) for its UI framework. The reasons for this migration include:

- Smaller dependency footprint (Flet is much lighter than PySide6)
- Better cross-platform support (desktop and web)
- Modern UI components and Material Design
- Simpler reactive programming model

## 📦 Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Running the Application

```bash
python -m evrmail
```

## 🧩 Main Components

- **Inbox Panel**: View and manage received messages
- **Compose Panel**: Create and send new messages
- **Wallet Panel**: Manage EVR and asset balances
- **Browser Panel**: Browse Evrmore blockchain domains
- **Settings Panel**: Configure application settings
- **Log Panel**: View application logs

## 🏗️ Architecture

EvrMail uses a clean architecture with:

- **GUI Layer**: Flet UI components in `src/evrmail/gui/`
- **Business Logic**: Core messaging and blockchain logic
- **Data Layer**: Blockchain interaction, local storage, and IPFS

## 📚 Dependencies

- Flet: UI framework
- PyCryptodome: Cryptographic operations
- base58: Base58 encoding/decoding
- PyYAML: Configuration files
- requests: HTTP client
- python-dotenv: Environment management

## 📝 License

© 2025 Manticore Technologies, LLC

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


6. Making sure flet works:

/home/xoznir/.flet/bin/flet-0.27.6/flet/flet: error while loading shared libraries: libmpv.so.1: cannot open shared object file: No such file or directory

Install this package:

sudo apt-get update && sudo apt-get install -y libmpv-dev mpv