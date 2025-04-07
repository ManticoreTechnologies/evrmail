Here's a full `README.md` section for the `evrmail wallets` subcommands, with emoji-driven clarity and structured Markdown:

```markdown
# 👜 `evrmail wallets` — Wallet Management CLI

Manage your Evrmore HD wallets with intuitive commands. Create, list, export, inspect, and organize your wallets with ease.

---

## 🧭 Subcommands Overview

| Command | Description |
|--------|-------------|
| `evrmail wallets create` | 🛠️ Create a new wallet with a fresh mnemonic |
| `evrmail wallets list`   | 📂 List all saved wallets in your system |
| `evrmail wallets show`   | 📄 Show metadata and address info for a wallet |
| `evrmail wallets export` | 💾 Export a wallet's JSON data to a file |
| `evrmail wallets import` | 📥 (Coming soon) Import wallet from backup |

---

## 🛠️ Create a Wallet

```bash
# Create a new wallet named "phoenix"
$ evrmail wallets create phoenix

# Create with a passphrase (BIP39)
$ evrmail wallets create phoenix --pass "MySecret123"

# Output raw JSON data
$ evrmail wallets create phoenix --raw
```

---

## 📂 List Wallets

```bash
# Show all wallets stored in ~/.evrmail/wallets
$ evrmail wallets list

# Output as raw JSON array
$ evrmail wallets list --raw
```

---

## 📄 Show Wallet Metadata

```bash
# Show wallet info like creation date, xpub, file path
$ evrmail wallets show phoenix

# Output full wallet JSON
$ evrmail wallets show phoenix --raw

# Show first 5 derived addresses
$ evrmail wallets show phoenix --with-addresses

# Show balance summary for the wallet
$ evrmail wallets show phoenix --summary

# Combine options
$ evrmail wallets show phoenix --with-addresses --summary
```

---

## 💾 Export a Wallet

```bash
# Save wallet JSON to a backup file
$ evrmail wallets export phoenix --output phoenix.json

# Output wallet data to terminal instead of file
$ evrmail wallets export phoenix --raw
```

---

## 🔐 Security Notice

Your wallets are stored locally in:

```
~/.evrmail/wallets/<name>.json
```

Each file contains sensitive data such as:

- 🔑 Root private key (xprv)
- 🧠 Mnemonic phrase
- Derived addresses and keys

**Keep these files secure and back them up carefully!**

---

## 📌 Notes

- Wallet names should not contain spaces.
- Wallets are BIP44 HD wallets using coin type `175` (Evrmore).
- Derivation paths follow `m/44'/175'/0'/0/index`.

---

Ready to level up your wallet management?  
Start with:

```bash
evrmail wallets create yourname
```
