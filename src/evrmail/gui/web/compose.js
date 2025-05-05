// Compose view implementation
function initComposeView() {
  const view = document.getElementById('compose-view');
  
  // Create compose UI
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">📨 Compose New Message</h1>
      
      <form id="compose-form">
        <div class="mb-3">
          <label for="recipient" class="form-label">Recipient</label>
          <input type="text" class="form-control" id="recipient" placeholder="Enter recipient address" required>
        </div>
        
        <div class="mb-3">
          <label for="subject" class="form-label">Subject</label>
          <input type="text" class="form-control" id="subject" placeholder="Enter subject" required>
        </div>
        
        <div class="mb-3">
          <label for="outbox" class="form-label">Outbox Asset (optional)</label>
          <select class="form-select" id="outbox"></select>
          <div class="form-text">Leave blank to auto-select an outbox asset</div>
        </div>
        
        <div class="mb-3">
          <label for="message" class="form-label">Message</label>
          <textarea class="form-control" id="message" rows="10" placeholder="Write your message here..." required></textarea>
        </div>
        
        <div class="mb-3 form-check">
          <input type="checkbox" class="form-check-input" id="dry-run">
          <label class="form-check-label" for="dry-run">🧪 Dry-Run Only (simulate, no broadcast)</label>
        </div>
        
        <div id="status-message" class="alert d-none" role="alert"></div>
        
        <div class="text-center">
          <button type="submit" class="btn btn-primary">
            <i class="bi bi-send"></i> Send Message
          </button>
        </div>
      </form>
    </div>
  `;
  
  // Load available outbox assets
  loadOutboxAssets();
  
  // Set up form submission handler
  document.getElementById('compose-form').addEventListener('submit', sendMessage);
}

// Load available outbox assets
function loadOutboxAssets() {
  const outboxSelect = document.getElementById('outbox');
  
  // Add empty option for auto-select
  const emptyOption = document.createElement('option');
  emptyOption.value = "";
  emptyOption.textContent = "(Auto-Select Outbox)";
  outboxSelect.appendChild(emptyOption);
  
  // Fetch assets from wallet
  eel.get_wallet_balances()().then(balances => {
    if (balances && balances.assets) {
      // Get asset names and add them to dropdown
      const assetNames = Object.keys(balances.assets);
      
      if (assetNames.length > 0) {
        assetNames.sort().forEach(asset => {
          const option = document.createElement('option');
          option.value = asset;
          option.textContent = asset;
          outboxSelect.appendChild(option);
        });
      } else {
        // No assets found, add a placeholder
        const noAssetsOption = document.createElement('option');
        noAssetsOption.value = "";
        noAssetsOption.textContent = "(No assets available)";
        noAssetsOption.disabled = true;
        outboxSelect.appendChild(noAssetsOption);
      }
    }
  }).catch(error => {
    console.error("Error loading assets:", error);
  });
}

// Send message function
function sendMessage(e) {
  e.preventDefault();
  
  // Get form values
  const recipient = document.getElementById('recipient').value.trim();
  const subject = document.getElementById('subject').value.trim();
  const message = document.getElementById('message').value.trim();
  const outbox = document.getElementById('outbox').value.trim();
  const dryRun = document.getElementById('dry-run').checked;
  
  // Validate inputs
  if (!recipient || !subject || !message) {
    showStatus('Please fill in all required fields', 'danger');
    return;
  }
  
  // Show sending status
  showStatus('⏳ Sending message...', 'warning');
  
  // Disable submit button
  const submitButton = document.querySelector('#compose-form button[type="submit"]');
  submitButton.disabled = true;
  submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
  
  // Call backend to send message
  eel.send_message(recipient, subject, message, outbox, dryRun)().then(result => {
    // Re-enable submit button
    submitButton.disabled = false;
    submitButton.innerHTML = '<i class="bi bi-send"></i> Send Message';
    
    if (result.success) {
      // Show success message
      showStatus(`✅ ${result.message}`, 'success');
      
      // Show txid if available
      if (result.txid) {
        const statusElement = document.getElementById('status-message');
        const txidElement = document.createElement('div');
        txidElement.className = 'mt-2 small';
        txidElement.innerHTML = `Transaction ID: <code>${result.txid}</code>`;
        statusElement.appendChild(txidElement);
      }
      
      // Clear form for new message
      if (!dryRun) {
        setTimeout(() => {
          document.getElementById('recipient').value = '';
          document.getElementById('subject').value = '';
          document.getElementById('message').value = '';
          // Keep outbox and dry-run settings
        }, 3000);
      }
    } else {
      // Show error message
      showStatus(`❌ Error: ${result.error}`, 'danger');
    }
  }).catch(error => {
    // Re-enable submit button
    submitButton.disabled = false;
    submitButton.innerHTML = '<i class="bi bi-send"></i> Send Message';
    
    // Show error message
    showStatus(`❌ Error: ${error.message || 'Unknown error'}`, 'danger');
    console.error('Send message error:', error);
  });
}

// Show status message
function showStatus(message, type) {
  const statusElement = document.getElementById('status-message');
  statusElement.className = `alert alert-${type}`;
  statusElement.textContent = message;
  statusElement.classList.remove('d-none');
  
  // Scroll to status message
  statusElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
} 