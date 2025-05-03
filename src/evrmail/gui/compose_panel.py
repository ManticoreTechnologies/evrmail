# evrmail/gui/compose_panel.py

import flet as ft
from evrmail.wallet.utils import calculate_balances
from pathlib import Path
import json
from datetime import datetime

def save_sent_message(to, subject, content, txid, dry_run=False):
    SENT_FILE = Path.home() / ".evrmail" / "sent.json"
    SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SENT_FILE.exists():
        sent = json.loads(SENT_FILE.read_text())
    else:
        sent = []

    sent.append({
        "to": to,
        "subject": subject,
        "content": content,
        "txid": txid,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
    })

    SENT_FILE.write_text(json.dumps(sent, indent=2))

def create_compose_panel():
    """Create the compose email panel using Flet"""
    
    # Input fields
    to_field = ft.TextField(
        label="Recipient",
        hint_text="Address or Contact Name",
        border_color="#3ea6ff",
        expand=True,
    )
    
    subject_field = ft.TextField(
        label="Subject",
        hint_text="Enter subject...",
        border_color="#3ea6ff",
        expand=True,
    )
    
    message_field = ft.TextField(
        label="Message",
        multiline=True,
        min_lines=10,
        max_lines=20,
        hint_text="Write your message here...",
        border_color="#3ea6ff",
        expand=True,
    )
    
    # Calculate wallet balances to get available outboxes
    balances = calculate_balances()
    
    # Outbox dropdown
    outbox_dropdown = ft.Dropdown(
        label="Select Outbox",
        hint_text="Choose outbox or auto-select",
        options=[
            ft.dropdown.Option("(Auto-Select Outbox)"),
        ] + [
            ft.dropdown.Option(asset_name) for asset_name in balances["assets"].keys()
        ],
        width=400,
    )
    
    # Dry-run checkbox
    dry_run_checkbox = ft.Checkbox(
        label="🧪 Dry-Run Only (simulate, no broadcast)",
        value=False,
    )
    
    # Status message
    status_text = ft.Text(
        value="",
        color="#3ea6ff",
    )
    
    def handle_send(e):
        """Process the send message action"""
        from evrmail.commands.send.send_msg import send_msg_core
        
        to = to_field.value.strip() if to_field.value else ""
        subject = subject_field.value.strip() if subject_field.value else ""
        content = message_field.value.strip() if message_field.value else ""
        outbox = outbox_dropdown.value
        dry_run = dry_run_checkbox.value
        
        # Validate fields
        if not to or not subject or not content:
            status_text.value = "❌ Please fill out all required fields"
            status_text.color = "red"
            status_text.update()
            return
        
        # Use auto-select if that's chosen
        if outbox == "(Auto-Select Outbox)":
            outbox = None
        
        try:
            # Show sending status
            status_text.value = "⏳ Sending message..."
            status_text.color = "orange"
            status_text.update()
            
            # Send the message
            txid = send_msg_core(
                to=to,
                outbox=outbox,
                subject=subject,
                content=content,
                fee_rate=0.01,
                dry_run=dry_run,
                debug=False,
                raw=False
            )
            
            # Save the sent message
            save_sent_message(to, subject, content, txid, dry_run=dry_run)
            
            # Update status based on result
            if dry_run:
                status_text.value = "✅ Dry-Run Accepted (No broadcast made)"
            else:
                status_text.value = f"✅ Message Sent! TXID: {txid[:10]}..."
            status_text.color = "#4caf50"
            
            # Clear form
            to_field.value = ""
            subject_field.value = ""
            message_field.value = ""
            outbox_dropdown.value = "(Auto-Select Outbox)"
            dry_run_checkbox.value = False
            
            # Update UI
            to_field.update()
            subject_field.update()
            message_field.update()
            outbox_dropdown.update()
            dry_run_checkbox.update()
            status_text.update()
            
        except Exception as e:
            # Show error
            status_text.value = f"❌ Error: {str(e)}"
            status_text.color = "red"
            status_text.update()
    
    # Send button
    send_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.SEND),
                ft.Text("Send Message", size=16, weight="bold")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        bgcolor="#3ea6ff",
        color="black",
        on_click=handle_send,
        width=250,
    )
    
    # Build the panel
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        "📨 Compose New Message",
                        size=24, 
                        color="white",
                        weight="bold"
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20),
                ),
                to_field,
                subject_field,
                message_field,
                ft.Container(height=10),
                outbox_dropdown,
                dry_run_checkbox,
                status_text,
                ft.Container(
                    content=send_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=10,
            expand=True,
        ),
        padding=40,
        expand=True,
    )
    
    return panel
