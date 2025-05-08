import { loadTemplate } from '../../utils.js';

// import settingsTemplate from './settings.html'; // If using a bundler, otherwise use fetch

export async function initSettingsView() {
  await loadTemplate('components/Settings/settings.html', 'settings-view');
  // Set up event listeners and any initial logic here
  
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