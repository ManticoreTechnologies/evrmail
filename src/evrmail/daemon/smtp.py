import os
import time
import signal
from aiosmtpd.controller import Controller

MAILBOX_ROOT = "/home/cymos/mailbox"

class CustomHandler:
    async def handle_DATA(self, server, session, envelope):
        recipient = envelope.rcpt_tos[0]
        local_part = recipient.split('@')[0]
        mailbox_dir = os.path.join(MAILBOX_ROOT, local_part)
        os.makedirs(mailbox_dir, exist_ok=True)

        filename = os.path.join(mailbox_dir, f"msg-{int(time.time())}.eml")
        with open(filename, 'wb') as f:
            f.write(envelope.original_content)

        print(f"🔥 Received mail for {recipient} → {filename}")
        return '250 Message accepted for delivery'

# Global controller reference for signal handling
controller = None

def handle_exit(sig, frame):
    print("🛑 Stopping SMTP server...")
    if controller:
        controller.stop()
    exit(0)

def start_smtp_server():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    controller = Controller(CustomHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    print("📬 SMTP server running on port 25...")

    # Keep it running
    while True:
        time.sleep(1)


if __name__ == '__main__':
    start_smtp_server()