from fastapi import FastAPI, Request
from email.parser import BytesParser
from email.policy import default
import uvicorn
import time
from pathlib import Path
import email

app = FastAPI()
MAILBOX_ROOT = Path.home() / ".evrmail" / "mail"
MAILBOX_ROOT.mkdir(parents=True, exist_ok=True)

@app.post("/forward/{username}")
async def receive_email(username: str, request: Request):
    try:
        data = await request.json()
        to = data.get("to")
        sender = data.get("from")
        subject = data.get("subject", "(no subject)")
        raw = data.get("raw", "")

        try:
            parser = email.parser.Parser(policy=default)
            parser.parsestr(raw)
        except Exception as parse_err:
            print(f"⚠️ Email parse error: {parse_err}")

        mailbox_dir = MAILBOX_ROOT / username
        mailbox_dir.mkdir(parents=True, exist_ok=True)

        filename = mailbox_dir / f"msg-{int(time.time())}.eml"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(raw)

        print(f"🔥 Saved forwarded mail for {to} from {sender} → {filename}")
        return {"status": "stored"}

    except Exception as e:
        print(f"⚠️ Error processing mail for {username}: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    print("📡 EvrMail webhook server running on port 8025...")
    uvicorn.run(app, host="0.0.0.0", port=8025)
