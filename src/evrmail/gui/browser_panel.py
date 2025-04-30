# evrmail/gui/browser_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from evrmail.utils.ipfs import fetch_ipfs_json, fetch_ipfs_resource
from evrmail import rpc_client
import base64
import ecdsa
import hashlib
from pathlib import Path
import base58
import base64
from hashlib import sha256
from Crypto.Hash import RIPEMD160
from coincurve import PrivateKey, PublicKey
NO_SITE_FOUND_PATH = Path(__file__).parent / "no_payload.html"

def load_no_site_found_html() -> str:
    if NO_SITE_FOUND_PATH.exists():
        return NO_SITE_FOUND_PATH.read_text(encoding="utf-8")
    else:
        return "<h1>❌ Site not found</h1><p>Missing no_payload.html</p>"

NO_SITE_FOUND = load_no_site_found_html()
def pubkey_to_address(pubkey: bytes) -> str:
    """
    Hash160 + base58 for Evrmore P2PKH (prefix=0x21 => 'E').
    """
    h = sha256(pubkey).digest()
    r160 = RIPEMD160.new(h).digest()
    versioned = b'\x21' + r160  # 0x21 => "E"
    checksum = sha256(sha256(versioned).digest()).digest()[:4]
    return base58.b58encode(versioned + checksum).decode()

def base58_encode(b: bytes) -> str:
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(b, 'big')
    encode = ''
    while num > 0:
        num, rem = divmod(num, 58)
        encode = alphabet[rem] + encode
    # Handle leading zeros
    pad = 0
    for byte in b:
        if byte == 0:
            pad += 1
        else:
            break
    return '1' * pad + encode

def create_browser_panel() -> QWidget:
    panel = QWidget()
    main_layout = QVBoxLayout(panel)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    top_bar = QHBoxLayout()
    url_bar = QLineEdit()
    url_bar.setPlaceholderText("🔎 Enter Evrmail domain or URL...")
    url_bar.setStyleSheet("""
        QLineEdit {
            background-color: #181818;
            color: #eeeeee;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #3ea6ff;
            font-size: 16px;
        }
    """)

    esl_status = QLabel("")
    esl_status.setStyleSheet("color: #00e0b6; font-weight: bold; padding-left: 12px;")
    top_bar.addWidget(url_bar)
    top_bar.addWidget(esl_status)
    main_layout.addLayout(top_bar)

    browser = QWebEngineView()
    main_layout.addWidget(browser)

    def load_url():
        text = url_bar.text().strip()

        if text.endswith(".evr"):
            domain = text[:-4]
            try:
                asset_data = rpc_client.getassetdata(domain.upper())
                if not asset_data.get("has_ipfs"):
                    browser.setHtml(NO_SITE_FOUND_HTML)
                    return
                cid = asset_data.get("ipfs_hash")
                esl_payload = fetch_ipfs_json(cid)
                if not esl_payload:
                    browser.setHtml(f"<h1>❌ Failed to load ESL payload for {domain}.evr</h1>")
                    return

                # Validate ESL
                pubkey = esl_payload.get("site_pubkey")
                admin_asset = esl_payload.get("admin_asset") + "!"
                expected_address = pubkey_to_address(bytes.fromhex(pubkey))
                print(expected_address)
                owners = rpc_client.listaddressesbyasset(admin_asset)
                if expected_address in owners:
                    esl_status.setText("🛡️ ESL Verified")
                else:
                    esl_status.setText("⚠️ Unverified Site")

                # Load content
                content_cid = esl_payload.get("content_ipfs")
                content_type, data = fetch_ipfs_resource(content_cid)
                if content_type.startswith("text/html"):
                    browser.setHtml(data.decode('utf-8'))
                elif content_type.startswith("image/"):
                    b64 = base64.b64encode(data).decode('utf-8')
                    html = f"<html><body style='background:black;'><img src='data:{content_type};base64,{b64}' style='width:100%;height:auto;object-fit:contain;'/></body></html>"
                    browser.setHtml(html)
                else:
                    browser.setHtml(f"<h1>⚠ Unsupported content type: {content_type}</h1>")
            except Exception as e:
                browser.setHtml(f"<h1>❌ Failed to resolve {text}: {e}</h1>")
        else:
            if not text.startswith("http"):
                text = "https://" + text
            browser.setUrl(QUrl(text))

    url_bar.returnPressed.connect(load_url)

    browser.setUrl(QUrl("https://duckduckgo.com"))
    return panel
