## 📊 `evrmail balance` — Check Your EVR & Asset Holdings

Easily view EVR, asset, and UTXO balances from all your wallets and addresses.

### 🧰 Usage Examples

```bash
💳 Show total EVR balance:
$ evrmail balance

🔍 Show balance for a specific wallet:
$ evrmail balance --wallet fortress

📍 Show balance for a single address:
$ evrmail balance --address EVR...

🎯 Show balance of a specific asset:
$ evrmail balance --asset INFERNA

📦 Show all asset balances:
$ evrmail balance --assets

📊 Wallet stats (address count, total/received):
$ evrmail balance --summary

🗾 Show all unspent outputs (UTXOs):
$ evrmail balance --utxos

📄 Output raw JSON response:
$ evrmail balance --raw

Combine multiple options:
$ evrmail balance --wallet fortress --address EVR... --asset INFERNA --summary --utxos --raw
```

### 📦 Options

- `--wallet <wallet_name>`: Show balances for all addresses in a specific wallet
- `--address <address>`: Show balance for a single address
- `--asset <asset_name>`: Show balance for a specific asset
- `--assets`: Show all asset balances
- `--summary`: Show wallet stats (address count, total/received)
- `--utxos`: Show all unspent outputs (UTXOs)
- `--raw`: Output raw JSON response