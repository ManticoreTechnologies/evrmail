import asyncio
import os
import sys
import ssl
import time
import threading
import json
from aiosmtpd.controller import Controller
from email.message import EmailMessage
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import smtplib
import dns.resolver
import dkim

from evrmore_rpc import EvrmoreClient
from evrmail.utils.create_message_payload import create_message_payload
from evrmail.utils.create_batch_payload import create_batch_payload
from evrmail.utils.ipfs import add_to_ipfs
from evrmail.utils.scan_payload import scan_payload
from evrmail.utils.inbox import save_messages

# Load Evrmore RPC and validate connection
rpc_client = EvrmoreClient()
try:
    rpc_client.getblockcount()
except Exception as e:
    print(f"[EvrMail] ⚠️ Could not reach Evrmore node – {e}")
    sys.exit(1)

# Load config
CONFIG_PATH = Path.home() / ".evrmail" / "server_config.json"
if not CONFIG_PATH.exists():
    print(f"[EvrMail] ❌ Missing config file at {CONFIG_PATH}")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    config = json.load(f)

# Config values
DOMAIN = config.get("domain", "evrmail.com")
SMTP_PORT = config.get("smtp_port", 2525)
API_PORT = config.get("api_port", 8888)
DKIM_SELECTOR = config.get("dkim_selector", "default")
DKIM_KEY_PATH = config.get("dkim_private_key_path", "/root/.evrmail/dkim_private_key.pem")
ASSET_NAME = config.get("asset_name", "EVRMAIL~OUTBOX")  # Added asset name for messaging

# Paths
MAILBOX_ROOT = Path.home() / ".evrmail" / "mail"
VALID_USERS_FILE = Path("/root/.evrmail/valid_users.txt")
MAILBOX_ROOT.mkdir(parents=True, exist_ok=True)

active_clients = {}
app = FastAPI()

# ────────────────────────────────────────────────────────────────────────────────
# SMTP HANDLER
# ────────────────────────────────────────────────────────────────────────────────

class EvrMailHandler:
    async def handle_DATA(self, server, session, envelope):
        recipient = envelope.rcpt_tos[0]
        local_part, domain = recipient.split('@', 1)

        if domain == DOMAIN:
            try:
                with VALID_USERS_FILE.open("r") as f:
                    users = set(line.strip() for line in f if line.strip())
            except FileNotFoundError:
                users = set()

            if local_part not in users:
                print(f"Rejected unknown user: {recipient}")
                return "550 No such user here"

            mailbox_dir = MAILBOX_ROOT / local_part
            mailbox_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            filename = mailbox_dir / f"msg-{timestamp}.eml"

            try:
                with open(filename, "wb") as f:
                    f.write(envelope.original_content)
                print(f"📥 Saved mail for {recipient} -> {filename}")

                # Send the message to the blockchain
                my_message = create_message_payload(
                    local_part,  # To address (the local part of the email address)
                    "Subject here",  # Placeholder for subject
                    envelope.original_content.decode(errors="ignore")  # Body content
                )

                # Create a batch and send to blockchain
                my_batch = create_batch_payload([my_message])
                my_batch_cid = add_to_ipfs(my_batch)

                # Now scan the batch
                my_messages = scan_payload(my_batch_cid)
                save_messages(my_messages)  # Save to inbox

                return "250 OK"
            except Exception as e:
                print(f"❌ Failed to store message: {e}")
                return "550 Could not store message"

        return "550 Invalid domain"

# ────────────────────────────────────────────────────────────────────────────────
# API SCHEMA
# ────────────────────────────────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    address: str
    message: str
    signature: str

class SendEmailRequest(BaseModel):
    from_address: str
    to: str
    subject: str
    body: str
    signature: str

class SubassetPurchaseRequest(BaseModel):
    username: str
    payment_address: str
    amount: float
    signature: str

# ────────────────────────────────────────────────────────────────────────────────
# API ROUTES
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/register_email")
def register_email(req: EmailRequest):
    address = req.address.strip()
    expected_message = f"{DOMAIN}: Register address {address}"

    if not rpc_client.validateaddress(address).get("isvalid", False):
        return JSONResponse(status_code=400, content={"error": "Invalid address"})

    if req.message.strip() != expected_message:
        return JSONResponse(status_code=400, content={"error": f"Expected: `{expected_message}`"})

    if not rpc_client.verifymessage(address, req.signature, req.message):
        return JSONResponse(status_code=403, content={"error": "Invalid signature"})

    VALID_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    users = set()
    if VALID_USERS_FILE.exists():
        users.update(line.strip() for line in VALID_USERS_FILE.read_text().splitlines())

    if address in users:
        return JSONResponse(status_code=409, content={"error": "Already registered"})

    users.add(address)
    VALID_USERS_FILE.write_text("\n".join(sorted(users)))
    return {"message": f"Registered: {address}@{DOMAIN}", "username": address}

@app.post("/send_email")
def send_email(req: SendEmailRequest):
    expected_message = f"{DOMAIN}: Send mail from {req.from_address} to {req.to} subject {req.subject}"

    if not rpc_client.validateaddress(req.from_address).get("isvalid", False):
        return JSONResponse(status_code=400, content={"error": "Invalid from_address"})

    if not rpc_client.verifymessage(req.from_address, req.signature, expected_message):
        return JSONResponse(status_code=403, content={"error": "Signature does not match"})

    try:
        send_real_email(req.from_address, req.to, req.subject, req.body, DKIM_SELECTOR, DOMAIN, DKIM_KEY_PATH)
        return {"message": "Email sent."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/buy_subasset")
def buy_subasset(req: SubassetPurchaseRequest):
    # Here you would verify the payment via the Evrmore blockchain
    # For example, you could check the balance of the payment address:
    balance = rpc_client.get_balance(req.payment_address)
    if balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds.")

    # Now issue the subasset
    subasset_name = f"{ASSET_NAME}~{req.username}"
    
    # Use rpc_client to issue the subasset
    txid = rpc_client.issueunique(ASSET_NAME, [subasset_name], [], req.payment_address, req.payment_address)

    return {"message": f"Subasset {subasset_name} issued successfully.", "txid": txid}

# ────────────────────────────────────────────────────────────────────────────────
# EMAIL SENDER
# ────────────────────────────────────────────────────────────────────────────────

def send_real_email(from_addr, to_addr, subject, body, dkim_selector, dkim_domain, dkim_private_key_path):
    msg = EmailMessage()
    msg["From"] = f"{from_addr}@{dkim_domain}"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    with open(dkim_private_key_path, "rb") as f:
        private_key = f.read()

    dkim_header = dkim.sign(
        message=msg.as_bytes(),
        selector=dkim_selector.encode(),
        domain=dkim_domain.encode(),
        privkey=private_key,
        include_headers=[b"from", b"to", b"subject"]
    )

    raw_message = dkim_header + msg.as_bytes()

    recipient_domain = to_addr.split("@")[1]
    answers = dns.resolver.resolve(recipient_domain, 'MX')
    mx_record = sorted(answers, key=lambda r: r.preference)[0].exchange.to_text()

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with smtplib.SMTP(mx_record, 25, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.sendmail(f"{from_addr}@{dkim_domain}", [to_addr], raw_message)

    print(f"✅ Email sent to {to_addr} via {mx_record}")

# ────────────────────────────────────────────────────────────────────────────────
# RUN LOOP
# ────────────────────────────────────────────────────────────────────────────────

def run_mailserver():
    controller = Controller(handler=EvrMailHandler(), hostname="0.0.0.0", port=SMTP_PORT, ready_timeout=5)
    controller.start()
    print(f"📡 EvrMail SMTP running on port {SMTP_PORT}")
    return controller

def run_api():
    print(f"🧠 EvrMail API + WebSocket on http://0.0.0.0:{API_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)

async def amain():
    smtp_controller = run_mailserver()
    thread = threading.Thread(target=run_api, daemon=True)
    thread.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        smtp_controller.stop()

if __name__ == "__main__":
    asyncio.run(amain())
