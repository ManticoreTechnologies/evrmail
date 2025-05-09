"""
Debug utilities for testing and diagnosing contact request issues
"""

import json
import logging
from pathlib import Path
from evrmail.config import load_config, save_config
from evrmail.daemon import EVRMailDaemon
from evrmail.wallet.addresses import get_all_addresses

def debug_contact_request_flow(recipient_address=None, name="Test Contact"):
    """Test the full contact request flow and log detailed diagnostics"""
    logging.info("==== CONTACT REQUEST DEBUG FLOW ====")
    
    # 1. Load configuration
    config = load_config()
    logging.info(f"1. Loaded configuration, current contacts: {len(config.get('contacts', {}))}")
    logging.info(f"   Current contact requests: {len(config.get('contact_requests', {}))}")
    
    # 2. Get addresses
    addresses = get_all_addresses()
    logging.info(f"2. Available addresses: {len(addresses)}")
    if addresses:
        # Handle both string and dict formats
        if isinstance(addresses[0], dict):
            first_address = addresses[0]['address']
        else:
            first_address = addresses[0]
        logging.info(f"   First address: {first_address}")
    else:
        logging.error("   No addresses available!")
        return
    
    # Default to sending to ourselves if no recipient specified
    if not recipient_address:
        if isinstance(addresses[0], dict):
            recipient_address = addresses[0]['address']
        else:
            recipient_address = addresses[0]
        logging.info(f"   Using self-address as recipient: {recipient_address}")
    
    # 3. Create EVRMailDaemon
    daemon = EVRMailDaemon()
    logging.info("3. Created EVRMailDaemon instance")
    
    # 4. Send contact request
    try:
        logging.info(f"4. Sending contact request to {recipient_address}")
        result = daemon.send_contact_request(recipient_address, name)
        logging.info(f"   Contact request send result: {result}")
    except Exception as e:
        logging.error(f"   Error sending contact request: {e}")
        logging.error(f"   {traceback.format_exc()}")
    
    # 5. Check contact requests
    config = load_config()  # Reload to see changes
    logging.info(f"5. After sending, contact requests count: {len(config.get('contact_requests', {}))}")
    
    # 6. Create contact request message for manual testing
    try:
        # Handle both string and dict formats
        if isinstance(addresses[0], dict):
            sender_address = addresses[0]['address']
        else:
            sender_address = addresses[0]
            
        test_message = {
            "type": "contact_request",
            "from": sender_address,
            "to": recipient_address,
            "name": name,
            "encrypted": False,
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        # Try to process it directly
        logging.info("6. Manual contact request processing test:")
        logging.info(f"   Test message: {json.dumps(test_message, indent=2)}")
        
        result = daemon.process_contact_request(test_message)
        logging.info(f"   Manual processing result: {result}")
        
    except Exception as e:
        logging.error(f"   Error in manual processing: {e}")
        logging.error(f"   {traceback.format_exc()}")
    
    # 7. Final status
    config = load_config()
    logging.info("7. Final state:")
    logging.info(f"   Contacts: {json.dumps(config.get('contacts', {}), indent=2)}")
    logging.info(f"   Contact requests: {json.dumps(config.get('contact_requests', {}), indent=2)}")
    logging.info("==== DEBUG FLOW COMPLETE ====")

def clear_all_contact_requests():
    """Clear all contact requests for testing purposes"""
    config = load_config()
    original_count = len(config.get('contact_requests', {}))
    config['contact_requests'] = {}
    save_config(config)
    return f"Cleared {original_count} contact requests"

def add_test_contact_request(address, name="Test Contact"):
    """Add a test contact request manually"""
    if not address:
        return "Error: Address required"
        
    config = load_config()
    contact_requests = config.get('contact_requests', {})
    
    contact_requests[address] = {
        "name": name,
        "status": "pending"
    }
    
    config['contact_requests'] = contact_requests
    save_config(config)
    return f"Added test contact request for {address}"

if __name__ == "__main__":
    # Configure logging to see output
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run the debug flow
    debug_contact_request_flow() 