"""
📬 EvrMail Contacts Management

Commands for managing contacts and contact requests in EvrMail.
"""

import typer
import json
from pathlib import Path
from typing import Optional

from evrmail.config import load_config, save_config
from evrmail.crypto import validate_evr_address
from evrmail.utils import get_address

contacts_app = typer.Typer(
    name="contacts",
    help="Manage your EvrMail contacts and contact requests",
)

@contacts_app.command("list")
def list_contacts():
    """List all your contacts."""
    config = load_config()
    contacts = config.get("contacts", {})
    
    if not contacts:
        print("No contacts found.")
        return
        
    print("\nYour Contacts:")
    print("-" * 50)
    for address, info in contacts.items():
        print(f"Address: {address}")
        print(f"Name: {info.get('name', 'Unnamed')}")
        print(f"Public Key: {info.get('pubkey', 'Not shared')}")
        print("-" * 50)

@contacts_app.command("add")
def add_contact(
    address: str = typer.Argument(..., help="Evrmore address to add as contact"),
    name: Optional[str] = typer.Option(None, help="Name for this contact")
):
    """Add a new contact."""
    # Validate address
    result = validate_evr_address(address)
    if not result["isvalid"]:
        print(f"Error: Invalid Evrmore address: {address}")
        return
        
    config = load_config()
    contacts = config.get("contacts", {})
    
    if address in contacts:
        print(f"Contact {address} already exists.")
        return
        
    contacts[address] = {
        "name": name or "Unnamed",
        "pubkey": None,  # Will be filled when they accept contact request
        "status": "pending"  # pending, accepted, rejected
    }
    
    config["contacts"] = contacts
    save_config(config)
    print(f"Added {address} as a contact.")

@contacts_app.command("remove")
def remove_contact(
    address: str = typer.Argument(..., help="Evrmore address to remove")
):
    """Remove a contact."""
    config = load_config()
    contacts = config.get("contacts", {})
    
    if address not in contacts:
        print(f"Contact {address} not found.")
        return
        
    del contacts[address]
    config["contacts"] = contacts
    save_config(config)
    print(f"Removed {address} from contacts.")

@contacts_app.command("requests")
def list_requests():
    """List pending contact requests."""
    config = load_config()
    requests = config.get("contact_requests", {})
    
    if not requests:
        print("No pending contact requests.")
        return
        
    print("\nPending Contact Requests:")
    print("-" * 50)
    for address, info in requests.items():
        print(f"From: {address}")
        print(f"Name: {info.get('name', 'Unnamed')}")
        print(f"Public Key: {info.get('pubkey', 'Not shared')}")
        print("-" * 50)

@contacts_app.command("accept")
def accept_request(
    address: str = typer.Argument(..., help="Address of contact request to accept")
):
    """Accept a contact request."""
    config = load_config()
    requests = config.get("contact_requests", {})
    contacts = config.get("contacts", {})
    
    if address not in requests:
        print(f"No pending request from {address}")
        return
        
    # Move from requests to contacts
    contact_info = requests[address]
    contact_info["status"] = "accepted"
    contacts[address] = contact_info
    
    # Remove from requests
    del requests[address]
    
    # Update config
    config["contact_requests"] = requests
    config["contacts"] = contacts
    save_config(config)
    
    print(f"Accepted contact request from {address}")

@contacts_app.command("reject")
def reject_request(
    address: str = typer.Argument(..., help="Address of contact request to reject")
):
    """Reject a contact request."""
    config = load_config()
    requests = config.get("contact_requests", {})
    
    if address not in requests:
        print(f"No pending request from {address}")
        return
        
    # Remove from requests
    del requests[address]
    
    # Update config
    config["contact_requests"] = requests
    save_config(config)
    
    print(f"Rejected contact request from {address}")

__all__ = ["contacts_app"]