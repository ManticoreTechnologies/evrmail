import { loadTemplate } from '../../utils.js';

// Compose view implementation
export async function initComposeView() {
  await loadTemplate('components/Compose/compose.html', 'compose-view');
  
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