# 🏷️ `evrmail addresses` — Manage Addresses and Keys

This command group helps you manage your Evrmore wallet addresses, keys, and validation tools.

### 📜 Overview

You can use the `addresses` command to:

- 🔍 **List** all known addresses  
- 🔢 **Get** a specific derived address by wallet/index  
- ⭐ **Show or set** the currently active address  
- ✅ **Validate** an Evrmore address  
- 🔓 **Reveal** private keys (only for wallet-owned addresses)  
- 🔐 **View** the public key of an address  

---

### 🧰 Usage Examples

```bash
📂 List all addresses:
$ evrmail addresses list

📂 List addresses in a specific wallet:
$ evrmail addresses list --wallet Phoenix

🔢 Get address at index 2:
$ evrmail addresses get --wallet Phoenix --index 2

📦 Get address tied to asset (outbox):
$ evrmail addresses get --outbox EVRMAIL#PHOENIX

⭐ Show currently selected address:
$ evrmail addresses active

✍️ Set active address:
$ evrmail addresses use --address EVR...

✅ Validate an address:
$ evrmail addresses validate --address EVR...

🔓 Show private key (WIF):
$ evrmail addresses dumpprivkey --address EVR...

🔍 Show public key:
$ evrmail addresses publickey --address EVR...
```

---

### ⚙️ Options

Most subcommands support:

- `--raw` → Output raw JSON for scripting, parsing, or development
- `--wallet` → Specify which wallet the address should be derived from
- `--index` → Derivation index (only valid when used with `--wallet`)
- `--address` → Provide any Evrmore address directly

---

### ⚠️ Security Warning

> Use `dumpprivkey` with caution!  
> Revealing your private keys can compromise your wallet if mishandled.

---
