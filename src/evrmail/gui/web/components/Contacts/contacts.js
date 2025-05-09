import { loadTemplate } from '../../utils.js';

// Initialize the contacts view
export async function initContactsView() {
    await loadTemplate('components/Contacts/contacts.html', 'contacts-view');
    
    // Load initial data
    loadContacts();
    loadRequests();
    
    // Set up form submission
    const form = document.getElementById('add-contact-form');
    if (form) {
        form.addEventListener('submit', handleAddContact);
    }

    // Address selection logic
    setupAddressSelection();
    
    // Set up periodic refresh
    setInterval(() => {
        loadContacts();
        loadRequests();
    }, 30000); // Refresh every 30 seconds

    console.log("Contacts view initialized");
}

// Show notification
function showNotification(message, isError = false) {
    const notifArea = document.getElementById('notification-area') || createNotificationArea();
    const notif = document.createElement('div');
    notif.className = `alert ${isError ? 'alert-danger' : 'alert-success'} mt-3`;
    notif.textContent = message;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notif.style.opacity = '0';
        setTimeout(() => notif.remove(), 500);
    }, 5000);
    
    notifArea.appendChild(notif);
    
    // Log to console for debugging
    if (isError) {
        console.error(message);
    } else {
        console.log(message);
    }
}

// Create notification area if it doesn't exist
function createNotificationArea() {
    const container = document.querySelector('.container');
    const notifArea = document.createElement('div');
    notifArea.id = 'notification-area';
    notifArea.style.position = 'fixed';
    notifArea.style.bottom = '20px';
    notifArea.style.right = '20px';
    notifArea.style.zIndex = '1000';
    container.appendChild(notifArea);
    return notifArea;
}

// Address selection logic
async function setupAddressSelection() {
    const specifyRadio = document.getElementById('addr-mode-specify');
    const dropdown = document.getElementById('specify-address-dropdown');
    const radios = document.getElementsByName('address-mode');

    // Populate dropdown
    const addresses = await eel.get_wallet_addresses()();
    dropdown.innerHTML = '';
    addresses.forEach(addr => {
        const opt = document.createElement('option');
        opt.value = addr.address;
        opt.textContent = `${addr.address} ${addr.label ? '(' + addr.label + ')' : ''}`;
        dropdown.appendChild(opt);
    });

    // Show/hide dropdown
    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (specifyRadio.checked) {
                dropdown.style.display = '';
            } else {
                dropdown.style.display = 'none';
            }
        });
    });
    // Initial state
    if (specifyRadio.checked) {
        dropdown.style.display = '';
    } else {
        dropdown.style.display = 'none';
    }
}

// Load contacts list
async function loadContacts() {
    const contactsList = document.getElementById('contacts-list');
    if (!contactsList) return;
    
    // Show loading indicator
    contactsList.innerHTML = '<p class="text-center"><i class="spinner"></i> Loading contacts...</p>';
    
    try {
        const contactsObj = await eel.get_contacts()();
        
        // Convert object of contacts to array for easier rendering
        const contacts = Object.entries(contactsObj || {}).map(([address, info]) => ({
            address: address,
            ...info
        }));
        
        if (contacts && contacts.length > 0) {
            contactsList.innerHTML = contacts.map(contact => `
                <div class="contact-item">
                    <div class="contact-info">
                        <h6>${contact.name || 'Unnamed'}</h6>
                        <small class="text-muted">${contact.address}</small>
                        ${contact.pubkey ? `<small class="text-success">Has public key</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="removeContact('${contact.address}')">
                        Remove
                    </button>
                </div>
            `).join('');
        } else {
            contactsList.innerHTML = '<p class="text-muted text-center">No contacts yet</p>';
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
        contactsList.innerHTML = '<p class="text-danger text-center">Error loading contacts</p>';
    }
}

// Load contact requests
async function loadRequests() {
    const requestsList = document.getElementById('contact-requests-list');
    if (!requestsList) return;
    
    // Show loading indicator
    requestsList.innerHTML = '<p class="text-center"><i class="spinner"></i> Loading requests...</p>';
    
    try {
        const requestsObj = await eel.get_contact_requests()();
        
        // Convert object of requests to array for easier rendering
        const requests = Object.entries(requestsObj || {}).map(([address, info]) => ({
            address: address,
            ...info
        }));
        
        if (requests && requests.length > 0) {
            requestsList.innerHTML = requests.map(request => `
                <div class="request-item">
                    <div class="request-info">
                        <h6>${request.name || 'Unnamed'}</h6>
                        <small class="text-muted">${request.address}</small>
                        ${request.pubkey ? `<small class="text-success">Has public key</small>` : ''}
                    </div>
                    <div class="request-actions">
                        <button class="btn btn-sm btn-success me-2" onclick="acceptRequest('${request.address}')">
                            Accept
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="rejectRequest('${request.address}')">
                            Reject
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            requestsList.innerHTML = '<p class="text-muted text-center">No pending contact requests</p>';
        }
    } catch (error) {
        console.error('Error loading contact requests:', error);
        requestsList.innerHTML = '<p class="text-danger text-center">Error loading contact requests</p>';
    }
}

// Handle add contact form submission
async function handleAddContact(event) {
    event.preventDefault();
    
    const address = document.getElementById('contact-address').value;
    const name = document.getElementById('contact-name').value;
    const radios = document.getElementsByName('address-mode');
    const dryRun = document.getElementById('dry-run-checkbox').checked;
    let addressMode = 'random';
    let fromAddress = null;
    
    // Get the selected address mode
    radios.forEach(radio => {
        if (radio.checked) addressMode = radio.value;
    });
    
    // If specifying address, get the selected one
    if (addressMode === 'specify') {
        fromAddress = document.getElementById('specify-address-dropdown').value;
        if (!fromAddress) {
            showNotification('Please select a specific address', true);
            return;
        }
    }
    
    // Validate input
    if (!address) {
        showNotification('Please enter an Evrmore address', true);
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="spinner"></i> Sending...';
    
    try {
        const result = await eel.send_contact_request(address, name, addressMode, fromAddress, dryRun)();
        if (result.success) {
            if (dryRun) {
                showNotification('Dry run successful! No transaction was broadcast.');
            } else {
                showNotification('Contact request sent successfully!');
                document.getElementById('add-contact-form').reset();
            }
            // Refresh contacts after a short delay to allow daemon to process
            setTimeout(() => {
                loadContacts();
                loadRequests();
            }, 2000);
        } else {
            showNotification(`Error: ${result.error}`, true);
        }
    } catch (error) {
        console.error('Error sending contact request:', error);
        showNotification('Error sending contact request: ' + (error.message || error), true);
    } finally {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Remove a contact
async function removeContact(address) {
    if (!confirm('Are you sure you want to remove this contact?')) return;
    
    try {
        const result = await eel.remove_contact(address)();
        if (result.success) {
            showNotification('Contact removed successfully');
            loadContacts();
        } else {
            showNotification(`Error: ${result.error}`, true);
        }
    } catch (error) {
        console.error('Error removing contact:', error);
        showNotification('Error removing contact', true);
    }
}

// Accept a contact request
async function acceptRequest(address) {
    try {
        const result = await eel.accept_contact_request(address)();
        if (result.success) {
            showNotification('Contact request accepted');
            loadContacts();
            loadRequests();
        } else {
            showNotification(`Error: ${result.error}`, true);
        }
    } catch (error) {
        console.error('Error accepting contact request:', error);
        showNotification('Error accepting contact request', true);
    }
}

// Reject a contact request
async function rejectRequest(address) {
    if (!confirm('Are you sure you want to reject this contact request?')) return;
    
    try {
        const result = await eel.reject_contact_request(address)();
        if (result.success) {
            showNotification('Contact request rejected');
            loadRequests();
        } else {
            showNotification(`Error: ${result.error}`, true);
        }
    } catch (error) {
        console.error('Error rejecting contact request:', error);
        showNotification('Error rejecting contact request', true);
    }
}

// Make functions available globally
window.removeContact = removeContact;
window.acceptRequest = acceptRequest;
window.rejectRequest = rejectRequest;

// Manage address dropdown visibility for the "specify" option
function setupAddressModeHandlers() {
    const addressSelector = document.getElementById('specify-address-selector');
    const addressDropdown = document.getElementById('specify-address-dropdown');
    
    if (!addressSelector || !addressDropdown) {
        console.error("Address selector elements not found");
        return;
    }
    
    // Hide by default
    addressSelector.style.display = 'none';
    
    // Listen to radio button changes
    document.querySelectorAll('input[name="address-mode"]').forEach(radio => {
        radio.addEventListener('change', e => {
            if (e.target.value === 'specify') {
                addressSelector.style.display = 'block';
                loadAddressDropdown();
            } else {
                addressSelector.style.display = 'none';
            }
        });
    });
}

// Load wallet addresses for the dropdown
async function loadAddressDropdown() {
    const dropdown = document.getElementById('specify-address-dropdown');
    if (!dropdown) return;
    
    dropdown.innerHTML = '<option value="">Loading addresses...</option>';
    
    try {
        const addresses = await eel.get_wallet_addresses()();
        
        if (addresses && addresses.length > 0) {
            dropdown.innerHTML = '<option value="">Select an address</option>';
            addresses.forEach(addr => {
                const option = document.createElement('option');
                option.value = addr.address;
                option.textContent = addr.label ? `${addr.label} (${addr.address})` : addr.address;
                dropdown.appendChild(option);
            });
        } else {
            dropdown.innerHTML = '<option value="">No addresses available</option>';
        }
    } catch (error) {
        console.error('Error loading addresses:', error);
        dropdown.innerHTML = '<option value="">Error loading addresses</option>';
    }
}

// Debug helper function
function logContactsData() {
    console.log("Debugging contacts data:");
    
    // Get and log contacts
    eel.get_contacts()().then(contacts => {
        console.log("Contacts data:", contacts);
    }).catch(err => {
        console.error("Error fetching contacts:", err);
    });
    
    // Get and log contact requests
    eel.get_contact_requests()().then(requests => {
        console.log("Contact requests data:", requests);
    }).catch(err => {
        console.error("Error fetching contact requests:", err);
    });
} 