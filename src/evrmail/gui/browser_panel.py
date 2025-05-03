# evrmail/gui/browser_panel.py

import flet as ft
from pathlib import Path
from evrmail.utils.ipfs import fetch_ipfs_json, fetch_ipfs_resource, fetch_ipns_resource
from evrmail import rpc_client
import base64
import hashlib
from Crypto.Hash import RIPEMD160
import base58

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
    h = hashlib.sha256(pubkey).digest()
    r160 = RIPEMD160.new(h).digest()
    versioned = b'\x21' + r160  # 0x21 => "E"
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return base58.b58encode(versioned + checksum).decode()

def create_browser_panel():
    """Create a simplified browser panel for Evrnet domains"""
    
    # URL input field
    url_bar = ft.TextField(
        hint_text="🔎 Enter EvrNet domain (e.g. chess.evr)...",
        border_color="#3ea6ff",
        expand=True,
        border_radius=8,
        prefix_icon=ft.icons.SEARCH,
    )
    
    # ESL status display
    esl_status = ft.Text(
        value="",
        color="#3ea6ff",
        weight="bold",
        size=14,
    )
    
    # Content display area (since we can't use a real browser in Flet)
    content_display = ft.Container(
        content=ft.Column(
            [
                ft.Text("Enter an Evrmore domain above to browse", 
                       color="#ccc", 
                       text_align=ft.TextAlign.CENTER,
                       size=18),
                ft.Text("Example: chess.evr", 
                        color="#3ea6ff", 
                        text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        bgcolor="#121212",
        border_radius=8,
        expand=True,
        border=ft.border.all(color="#333", width=1),
    )
    
    def load_url(e=None):
        """Handle loading a domain from the URL bar"""
        text = url_bar.value.strip() if url_bar.value else ""
        
        # Clear current content
        content_display.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        
        if text.endswith(".evr"):
            domain = text[:-4]
            esl_status.value = "⏳ Loading..."
            esl_status.update()
            
            try:
                # Get asset data from the blockchain
                asset_data = rpc_client.getassetdata(domain.upper())
                if not asset_data.get("has_ipfs"):
                    content_display.content = ft.Column(
                        [
                            ft.Icon(ft.icons.ERROR, color="red", size=40),
                            ft.Text("No IPFS payload found", color="white", size=20),
                            ft.Text(f"The domain {text} exists but has no content", color="#ccc"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    )
                    esl_status.value = "❌ No IPFS payload"
                    esl_status.update()
                    content_display.update()
                    return
                
                # Get ESL payload from IPFS
                cid = asset_data.get("ipfs_hash")
                esl_payload = fetch_ipfs_json(cid)
                if not esl_payload:
                    content_display.content = ft.Column(
                        [
                            ft.Icon(ft.icons.ERROR, color="red", size=40),
                            ft.Text(f"ESL not found for {domain}.evr", color="white", size=20),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                    esl_status.value = "❌ Invalid ESL"
                    esl_status.update()
                    content_display.update()
                    return
                
                # Verify ESL ownership
                pubkey = esl_payload.get("site_pubkey")
                admin_asset = esl_payload.get("admin_asset") + "!"
                expected_address = pubkey_to_address(bytes.fromhex(pubkey))
                owners = rpc_client.listaddressesbyasset(admin_asset)
                
                if expected_address in owners:
                    esl_status.value = "🛡️ ESL Verified"
                else:
                    esl_status.value = "⚠️ ESL Unverified"
                esl_status.update()
                
                # Show content info
                content_ipns = esl_payload.get("content_ipns")
                content_cid = esl_payload.get("content_ipfs")
                
                # In a real implementation, we would fetch and display the content
                # Here we just show placeholder info
                content_display.content = ft.Column(
                    [
                        ft.Text(f"Domain: {text}", size=20, color="white"),
                        ft.Text(f"IPFS Asset CID: {cid[:20]}...", color="#ccc"),
                        ft.Text(f"Content {'IPNS' if content_ipns else 'IPFS'}: " + 
                                f"{content_ipns[:20] + '...' if content_ipns else content_cid[:20] + '...'}",
                                color="#ccc"),
                        ft.Container(height=20),
                        ft.Icon(ft.icons.WEB, color="#3ea6ff", size=40),
                        ft.Text("Content would be displayed here", color="white", size=16),
                        ft.Text("Flet doesn't have a built-in web browser component", color="#ccc"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                )
                content_display.update()
                
            except Exception as e:
                content_display.content = ft.Column(
                    [
                        ft.Icon(ft.icons.ERROR, color="red", size=40),
                        ft.Text(f"Failed to load {text}", color="white", size=20),
                        ft.Text(str(e), color="#ccc"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                )
                esl_status.value = "❌ Load failed"
                esl_status.update()
                content_display.update()
        else:
            # For non-EVR domains, just show a message
            url = text if text.startswith("http") else f"https://{text}"
            content_display.content = ft.Column(
                [
                    ft.Icon(ft.icons.WEB, color="#3ea6ff", size=40),
                    ft.Text("External Web Content", color="white", size=20),
                    ft.Text(f"URL: {url}", color="#ccc"),
                    ft.Text("Flet doesn't have a built-in web browser component", color="#ccc"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )
            esl_status.value = "🌐 Web URL"
            esl_status.update()
            content_display.update()
    
    # Connect the enter key to the load function
    url_bar.on_submit = load_url
    
    # Create a refresh button
    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        tooltip="Refresh",
        on_click=load_url,
    )
    
    # Top bar with URL input and status
    top_bar = ft.Row(
        [
            url_bar,
            refresh_button,
            esl_status,
        ],
        spacing=10,
    )
    
    # Combine everything into the panel
    panel = ft.Container(
        content=ft.Column(
            [
                top_bar,
                content_display,
            ],
            spacing=10,
            expand=True,
        ),
        padding=20,
        expand=True,
    )
    
    return panel
