// Settings view implementation
function initSettingsView() {
  const view = document.getElementById('settings-view');
  
  // Create settings form
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">⚙️ Settings</h1>
      
      <div class="card">
        <div class="card-body">
          <form id="settings-form">
            <h4 class="text-primary mb-3">Connection Settings</h4>
            <div class="mb-4">
              <label for="rpc-url" class="form-label">Custom Node URL</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-hdd-network"></i></span>
                <input type="text" class="form-control" id="rpc-url" placeholder="e.g. https://rpc.evrmore.exchange">
              </div>
              <div class="form-text">Leave empty to use the default public node</div>
            </div>
            
            <hr>
            
            <h4 class="text-primary mb-3">Application Settings</h4>
            <div class="mb-3">
              <label for="max-addresses" class="form-label">Maximum Addresses</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-grid-3x3"></i></span>
                <input type="number" class="form-control" id="max-addresses" placeholder="e.g. 1000" min="10" step="10">
              </div>
            </div>
            
            <div class="mb-3">
              <label for="theme" class="form-label">Theme</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-palette"></i></span>
                <select class="form-select" id="theme">
                  <option value="dark">Dark Theme</option>
                  <option value="light">Light Theme</option>
                  <option value="system">System Default</option>
                </select>
              </div>
            </div>
            
            <div class="mb-4 form-check">
              <input type="checkbox" class="form-check-input" id="start-on-boot">
              <label class="form-check-label" for="start-on-boot">Start EvrMail on system boot</label>
            </div>
            
            <div id="settings-status" class="alert d-none" role="alert"></div>
            
            <div class="text-center">
              <button type="submit" class="btn btn-primary">
                <i class="bi bi-save"></i> Save Settings
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
  
  // Load settings
  loadSettings();
  
  // Set up form submission
  const form = document.getElementById('settings-form');
  form.addEventListener('submit', saveSettings);
}

// Load settings
function loadSettings() {
  eel.get_settings()().then(settings => {
    // Fill the form with loaded settings
    document.getElementById('rpc-url').value = settings.rpc_url || '';
    document.getElementById('max-addresses').value = settings.max_addresses || 1000;
    document.getElementById('theme').value = settings.theme || 'dark';
    document.getElementById('start-on-boot').checked = settings.start_on_boot || false;
  });
}

// Save settings
function saveSettings(e) {
  e.preventDefault();
  
  // Get form values
  const settings = {
    rpc_url: document.getElementById('rpc-url').value,
    max_addresses: parseInt(document.getElementById('max-addresses').value) || 1000,
    theme: document.getElementById('theme').value,
    start_on_boot: document.getElementById('start-on-boot').checked
  };
  
  // Show saving status
  const statusElement = document.getElementById('settings-status');
  statusElement.className = 'alert alert-warning';
  statusElement.textContent = '⏳ Saving settings...';
  statusElement.classList.remove('d-none');
  
  // Save settings
  eel.save_settings(settings)().then(result => {
    if (result.success) {
      // Show success message
      statusElement.className = 'alert alert-success';
      statusElement.textContent = '✅ Settings saved successfully';
      
      // Apply theme if changed
      applyTheme(settings.theme);
    } else {
      // Show error message
      statusElement.className = 'alert alert-danger';
      statusElement.textContent = `❌ Error: ${result.error || 'Failed to save settings'}`;
    }
  });
}

// Apply theme
function applyTheme(theme) {
  // In a real implementation, this would change the theme
  // For this demo, just log the theme change
  console.log(`Theme changed to: ${theme}`);
} 