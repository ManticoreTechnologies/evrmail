# 📬 EvrMail

A secure, blockchain-native email system built on the Evrmore blockchain, providing encrypted, decentralized communication.

## 📋 What is EvrMail?

EvrMail is a revolutionary email system that bridges the gap between blockchain and traditional email. Unlike conventional email services that rely on centralized servers, EvrMail leverages the Evrmore blockchain and IPFS to create a decentralized, secure, and censorship-resistant communication platform.

### How It Works in Simple Terms

- **Decentralized Storage**: Messages are stored on IPFS (InterPlanetary File System), not on corporate servers
- **Blockchain for Notifications**: The Evrmore blockchain is used to broadcast notifications about new messages, not to store the content itself
- **Asset-Based Outboxes**: EvrMail uses Evrmore blockchain assets as "outboxes" - own the asset, control who can send from it
- **Address-Based Inboxes**: Your Evrmore addresses function as inboxes for receiving messages
- **Bridge to Traditional Email**: Through evrmail.com, blockchain emails can be sent to and received from regular email addresses (gmail, outlook, etc.)
- **Self-Sovereign Identity**: You own your identity and communications - no account to create, no password to remember, just your blockchain keys
- **No Central Server Required**: The combination of blockchain and IPFS eliminates the need for centralized servers
- **Seamless Multi-Wallet Support**: Use multiple wallets simultaneously or import existing ones with just a few clicks - the most user-friendly wallet management in the Evrmore ecosystem
- **Built-in Spam Protection**: Communication requires public key exchange first - no more unsolicited messages from unknown senders

### Current Status & Roadmap

✅ **Completed (v0.1.0)**:
- Core protocol implementation
- End-to-end encryption with secp256k1 ECDH + AES-GCM
- Asset-based outboxes and address-based inboxes
- Basic sending & receiving functionality
- Multi-wallet management system
- Contact book with public key exchange
- Local IPFS integration for message storage

🔄 **In Progress (v0.2.0 - Q3 2025)**:
- Message broadcasting to multiple recipients
- Improved UI/UX with Flet framework
- Performance optimizations for large mailboxes
- Enhanced message threading and conversation view
- Attachment support for documents and images

🚧 **Coming Soon (v0.3.0 - Q4 2025)**:
- Clearnet email bridging through evrmail.com
- Gateway for sending/receiving from traditional email services
- Message forwarding service for offline recipients
- Mobile applications (iOS and Android)

🔮 **Future Roadmap (v1.0 and beyond)**:
- Email-to-asset swaps & trading platform
- Public email groups & forums
- DAO governance for public channels
- Browser extension for web integration
- Advanced filtering and search capabilities
- Integration with other blockchain messaging systems

## 🔒 Key Features

- **Blockchain-native Messaging**: Uses Evrmore assets as outboxes and addresses as inboxes
- **End-to-End Encryption**: Messages are encrypted with secp256k1 ECDH + AES-GCM
- **Decentralized Storage**: IPFS integration for message storage and retrieval
- **Self-sovereign Identity**: Own your identity through blockchain asset ownership
- **Multi-wallet Support**: Create, import, and manage multiple wallet identities with ease
- **Modern UI**: Intuitive interface with support for desktop and web
- **Spam-Free Communication**: Exchange public keys before messaging - ensuring only wanted communications

## 🏗️ Architecture

EvrMail uses a clean, modular architecture:

- **Core**: Blockchain interaction, cryptography, and messaging protocol
- **GUI**: Modern interface using Flutter/Flet for cross-platform support
- **Daemon**: Background services for message syncing and notification
- **Storage**: IPFS integration for decentralized content storage

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install EvrMail
pip install evrmail
```

### Setup

```bash
# Create a wallet
evrmail wallets create

# Create an address for receiving messages
evrmail receive MyInbox

# Get your public key to share with contacts
evrmail addresses get MyInbox

# Add a contact
evrmail contacts add <ADDRESS> <PUBKEY> --friendly-name "Alice"
```

### Usage

```bash
# Start the GUI application
evrmail

# Or use CLI commands:
evrmail inbox list
evrmail compose
```

## 💡 How It Works

1. **Identity**: Each user controls a unique channel asset on the Evrmore blockchain
2. **Sending**: Messages are encrypted with the recipient's public key and stored on IPFS
3. **Notification**: A small blockchain transaction notifies the recipient of a new message
4. **Retrieval**: Recipients decrypt messages using their private keys

## 📚 Technical Stack

- **Cryptography**: secp256k1, ECDH, AES-GCM, HKDF
- **Blockchain**: Evrmore RPC, ZeroMQ for event monitoring
- **Storage**: IPFS for decentralized content storage
- **Frontend**: Flet (Flutter) for modern, responsive UI
- **Backend**: Python for business logic and blockchain interaction

## 📦 CLI Commands

```
evrmail --help                # Show all commands
evrmail wallets <subcommand>  # Manage wallets
evrmail addresses <subcommand> # Manage addresses
evrmail contacts <subcommand> # Manage contacts
evrmail compose               # Create a new message
evrmail inbox list            # List received messages
evrmail inbox open            # Open the inbox in GUI
evrmail daemon start/stop     # Control the background service
evrmail ipfs start/stop       # Control IPFS node
```

## 🔄 Development

```bash
# Clone the repository
git clone https://github.com/ManticoreTech/evrmail.git
cd evrmail

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python -m evrmail dev
```

*Manticore Technologies® is a registered trademark.*

## 📝 License

© 2025 Manticore Technologies, LLC®

---

EvrMail is a product of Manticore Technologies®, LLC. All rights reserved.