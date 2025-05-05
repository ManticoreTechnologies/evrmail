// Compose view implementation
function initComposeView() {
  const view = document.getElementById('compose-view');
  
  // Create compose form
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">📨 Compose New Message</h1>
      
      <div class="card">
        <div class="card-body">
          <form id="compose-form">
            <div class="mb-3">
              <label for="recipient" class="form-label">Recipient</label>
              <input type="text" class="form-control" id="recipient" placeholder="Address or Contact Name" required>
            </div>
            
            <div class="mb-3">
              <label for="subject" class="form-label">Subject</label>
              <input type="text" class="form-control" id="subject" placeholder="Enter subject..." required>
            </div>
            
            <div class="mb-3">
              <label for="message" class="form-label">Message</label>
              <textarea class="form-control" id="message" rows="10" placeholder="Write your message here..." required></textarea>
            </div>
            
            <div class="mb-3">
              <label for="outbox" class="form-label">Outbox</label>
              <select class="form-select" id="outbox">
                <option value="">(Auto-Select Outbox)</option>
                <!-- Options will be loaded dynamically -->
              </select>
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
      </div>
    </div>
  `;
  
  // Load outbox options
  loadOutboxOptions();
  
  // Set up form submission
  const form = document.getElementById('compose-form');
  form.addEventListener('submit', handleFormSubmit);
}

// Load outbox options
function loadOutboxOptions() {
  eel.get_wallet_balances()().then(balances => {
    const outboxSelect = document.getElementById('outbox');
    
    // Add asset options
    Object.keys(balances.assets).forEach(asset => {
      const option = document.createElement('option');
      option.value = asset;
      option.textContent = asset;
      outboxSelect.appendChild(option);
    });
  });
}

// Handle form submission
function handleFormSubmit(e) {
  e.preventDefault();
  
  // Get form values
  const recipient = document.getElementById('recipient').value;
  const subject = document.getElementById('subject').value;
  const message = document.getElementById('message').value;
  const outbox = document.getElementById('outbox').value;
  const dryRun = document.getElementById('dry-run').checked;
  
  // Show sending status
  const statusMessage = document.getElementById('status-message');
  statusMessage.className = 'alert alert-warning';
  statusMessage.textContent = '⏳ Sending message...';
  statusMessage.classList.remove('d-none');
  
  // Send message
  eel.send_message(recipient, subject, message, outbox, dryRun)().then(result => {
    if (result.success) {
      // Show success message
      statusMessage.className = 'alert alert-success';
      statusMessage.textContent = `✅ ${result.message}`;
      
      // Clear form after a delay
      setTimeout(() => {
        document.getElementById('recipient').value = '';
        document.getElementById('subject').value = '';
        document.getElementById('message').value = '';
        document.getElementById('outbox').value = '';
        document.getElementById('dry-run').checked = false;
      }, 3000);
    } else {
      // Show error message
      statusMessage.className = 'alert alert-danger';
      statusMessage.textContent = `❌ Error: ${result.error}`;
    }
  });
} 