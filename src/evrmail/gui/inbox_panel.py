import flet as ft
from pathlib import Path
import json

# 📂 Inbox/Sent storage
INBOX_FILE = Path.home() / ".evrmail" / "inbox.json"
SENT_FILE = Path.home() / ".evrmail" / "sent.json"

def load_messages(file_path):
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def create_inbox_panel():
    """Create the inbox panel using Flet components"""
    
    # Create panel container first, we'll add the ListView to it later
    panel = ft.Container(
        content=None,  # Will be populated after message_list is initialized
        padding=30,
        expand=True,
    )
    
    # Message view
    message_view = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=15,
        max_lines=25,
        value="",
        expand=True,
        text_size=14,
        bgcolor="#181818",
        color="#eeeeee",
        border_color="#333",
        border_width=1,
    )
    
    # Message list - initialize but don't populate yet
    message_list = ft.ListView(
        expand=1,
        spacing=2,
        padding=10,
        auto_scroll=True
    )
    
    def show_message(e):
        """Display the selected message content"""
        msg_data = e.control.data
        if msg_data:
            if msg_data["type"] == "received":
                message_view.value = f"📥 From: {msg_data['from']}\nSubject: {msg_data['subject']}\n\n{msg_data['body']}"
            elif msg_data["type"] == "sent":
                message_view.value = f"📤 To: {msg_data['to']}\nSubject: {msg_data['subject']}\n\n{msg_data['body']}"
            message_view.update()
    
    # Refresh button
    refresh_btn = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.REFRESH),
                ft.Text("Refresh", size=14)
            ],
            spacing=5,
        ),
        bgcolor="#3ea6ff",
        color="black",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )
    
    def refresh_inbox(e=None):
        """Load and display messages from the inbox and sent files"""
        # Clear existing messages
        message_list.controls.clear()
        
        # Load messages
        inbox_msgs = load_messages(INBOX_FILE)
        sent_msgs = load_messages(SENT_FILE)
        
        # 📥 Inbox Messages
        for msg in inbox_msgs:
            content = msg.get("content", {})
            sender = content.get("from", "Unknown")
            subject = content.get("subject", "(No Subject)")
            body = content.get("content", "(No Content)")
            
            msg_data = {
                "type": "received",
                "subject": subject,
                "from": sender,
                "body": body
            }
            
            message_item = ft.ListTile(
                leading=ft.Icon(ft.icons.INBOX, color="#3ea6ff"),
                title=ft.Text(f"{sender}", color="white"),
                subtitle=ft.Text(f"{subject}", color="#bbb"),
                selected=False,
                data=msg_data,
                on_click=show_message,
            )
            message_list.controls.append(message_item)
        
        # 📤 Sent Messages
        for msg in sent_msgs:
            is_dry_run = msg.get("dry_run", False)
            recipient = msg.get("to", "Unknown")
            subject = msg.get("subject", "(No Subject)")
            body = msg.get("content", "(No Content)")
            
            icon = ft.icons.SCIENCE if is_dry_run else ft.icons.SEND
            icon_color = "orange" if is_dry_run else "#3ea6ff"
            
            msg_data = {
                "type": "sent",
                "subject": subject,
                "to": recipient,
                "body": body
            }
            
            message_item = ft.ListTile(
                leading=ft.Icon(icon, color=icon_color),
                title=ft.Text(f"To: {recipient}", color="white"),
                subtitle=ft.Text(f"{subject}", color="#bbb"),
                selected=False,
                data=msg_data,
                on_click=show_message,
            )
            message_list.controls.append(message_item)
        
        # Show a message if no messages are available
        if len(message_list.controls) == 0:
            message_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.WARNING, color="orange"),
                    title=ft.Text("No messages yet", color="#bbb"),
                )
            )
        
        # Update the list
        message_list.update()
    
    # Set up event handlers
    refresh_btn.on_click = refresh_inbox
    
    # Create main content column
    content_column = ft.Column(
        [
            ft.Container(
                content=ft.Text("📬 EvrMail Unified Inbox", 
                                size=24, 
                                color="white",
                                weight="bold"),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=20, bottom=10),
            ),
            ft.Container(
                content=message_list,
                border=ft.border.all(color="#333", width=1),
                border_radius=8,
                bgcolor="#181818",
                expand=3,
            ),
            message_view,
            ft.Container(
                content=refresh_btn,
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=10, bottom=20),
            ),
        ],
        spacing=16,
        expand=True,
    )
    
    # Set the content of the panel
    panel.content = content_column
    
    # Delay the refresh_inbox call until the widget is added to the page
    # We'll return a callback to do this work after the page is set up
    def refresh_after_mount():
        refresh_inbox()
    
    # Store the delayed init function in the panel object
    panel.delayed_init = refresh_after_mount
    
    return panel
