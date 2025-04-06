## 🚀 `evrmail send` — Send EVR, Assets, or Messages

Send EVR, transfer assets, or deliver encrypted messages via the Evrmore blockchain. Supports clearnet (`@email`) and on-chain addresses.

---

### 🧪 Example Commands

```bash
# ✉️ Send plain text metadata to a blockchain address
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Hello, world!"

# 🗃️ Load message body from a file
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body-file ./message.txt

# 🔐 Encrypt and send message
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Encrypted msg" --encrypt

# 📧 Send to clearnet email (future support)
$ evrmail send --from MYADDR --to user@example.com --outbox EVRMAIL#MYNAME --body "Hi from EvrMail"

# 🧪 Simulate send (don't broadcast)
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Just testing" --dry-run

# 📄 Output raw transaction JSON
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Test raw" --dry-run --raw

# 🐛 Debug mode (shows txid and raw hex)
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Debug test" --dry-run --debug
```markdown
## 🚀 `evrmail send` — Send EVR, Assets, or Messages

Send EVR, transfer assets, or deliver encrypted messages via the Evrmore blockchain. Supports clearnet (`@email`) and on-chain addresses.

---

### 🧪 Example Commands

```bash
# ✉️ Send plain text metadata to a blockchain address
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Hello, world!"

# 🗃️ Load message body from a file
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body-file ./message.txt

# 🔐 Encrypt and send message
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Encrypted msg" --encrypt

# 📧 Send to clearnet email (future support)
$ evrmail send --from MYADDR --to user@example.com --outbox EVRMAIL#MYNAME --body "Hi from EvrMail"

# 🧪 Simulate send (don't broadcast)
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Just testing" --dry-run

# 📄 Output raw transaction JSON
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Test raw" --dry-run --raw

# 🐛 Debug mode (shows txid and raw hex)
$ evrmail send --from MYADDR --to RECIPIENT --outbox EVRMAIL#MYNAME --body "Debug test" --dry-run --debug
```


### ⚙️ Options

| Option         | Description |
|----------------|-------------|
| `--from`       | 🔐 Your address (must be unlocked) |
| `--to`         | 🎯 Recipient address or email |
| `--outbox`     | 📦 Asset used for metadata messages (e.g. `EVRMAIL#YOURNAME`) |
| `--subject`    | 📝 Message subject line |
| `--body`       | ✏️ Inline message body |
| `--body-file`  | 📁 Load message content from a file |
| `--encrypt`    | 🔐 Encrypt the message using recipient's public key |
| `--reply-to`   | 🔁 Message ID being replied to |
| `--dry-run`    | 🧪 Simulate transaction, don't broadcast |
| `--debug`      | 🐛 Show TXID and raw hex transaction |
| `--raw`        | 📄 Output full JSON (use with `--dry-run`) |

---

### 📦 Notes

- Messages are embedded on-chain via metadata and can optionally be encrypted.
- All transactions use your chosen `--outbox` asset as a communication channel.
- Full asset or token transfer commands will be added under `send evr`, `send asset`, `send msg`.

```