#!/usr/bin/env python3
"""
Simple script to add a test contact request to the config file.
This bypasses the daemon's send_contact_request method for testing purposes.
"""

import sys
import json
from pathlib import Path
from evrmail.wallet.addresses import get_pubkey_for_address
def add_test_contact_request(address, name="Test Contact"):
    """Add a test contact request manually by modifying the config file directly."""
    config_path = Path.home() / ".evrmail" / "config.json"
    
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    contact_requests = config.get('contact_requests', {})
    
    # Skip if already in contacts
    contacts = config.get('contacts', {})
    if address in contacts:
        print(f"{address} already in contacts, skipping request")
        return
    
    # Skip if already a pending request
    if address in contact_requests:
        print(f"Contact request for {address} already pending")
        return
    
    # Add the request
    contact_requests[address] = {
        "name": name,
        "pubkey": get_pubkey_for_address(address),
        "status": "pending"
    }
    
    config["contact_requests"] = contact_requests
    
    # Save updated config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Successfully added test contact request for {address}")
    except Exception as e:
        print(f"Error saving config: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_test_contact.py <evrmore_address> [name]")
        sys.exit(1)
    
    address = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "Test Contact"
    
    add_test_contact_request(address, name) 