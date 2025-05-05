// Logs view implementation
function initLogsView() {
  const view = document.getElementById('logs-view');
  
  // Create logs UI
  view.innerHTML = `
    <div class="container">
      <div class="row mb-3">
        <div class="col">
          <h1>📜 Application Logs</h1>
        </div>
        <div class="col-auto">
          <button id="refresh-logs" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-clockwise"></i> Refresh
          </button>
        </div>
      </div>
      
      <div class="row mb-3">
        <div class="col-md-3">
          <label class="form-label">Categories</label>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="APP" id="category-app" checked>
            <label class="form-check-label" for="category-app">APP</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="GUI" id="category-gui" checked>
            <label class="form-check-label" for="category-gui">GUI</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="DAEMON" id="category-daemon" checked>
            <label class="form-check-label" for="category-daemon">DAEMON</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="WALLET" id="category-wallet" checked>
            <label class="form-check-label" for="category-wallet">WALLET</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="CHAIN" id="category-chain" checked>
            <label class="form-check-label" for="category-chain">CHAIN</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="NETWORK" id="category-network" checked>
            <label class="form-check-label" for="category-network">NETWORK</label>
          </div>
          <div class="form-check">
            <input class="form-check-input category-filter" type="checkbox" value="DEBUG" id="category-debug" checked>
            <label class="form-check-label" for="category-debug">DEBUG</label>
          </div>
        </div>
        
        <div class="col-md-3">
          <label class="form-label">Log Level</label>
          <select id="log-level" class="form-select">
            <option value="all" selected>All Levels</option>
            <option value="debug">Debug & Above</option>
            <option value="info">Info & Above</option>
            <option value="warning">Warning & Above</option>
            <option value="error">Error & Above</option>
            <option value="critical">Critical Only</option>
          </select>
        </div>
        
        <div class="col-md-6">
          <label class="form-label">Filter</label>
          <div class="input-group">
            <input type="text" id="log-filter" class="form-control" placeholder="Filter logs...">
            <button class="btn btn-outline-secondary" type="button" id="log-filter-clear">
              <i class="bi bi-x"></i>
            </button>
          </div>
        </div>
      </div>
      
      <div class="row mb-3">
        <div class="col">
          <div class="d-flex justify-content-between">
            <button id="clear-logs" class="btn btn-outline-danger">
              <i class="bi bi-trash"></i> Clear Display
            </button>
            <button id="save-logs" class="btn btn-outline-primary">
              <i class="bi bi-download"></i> Save Logs
            </button>
          </div>
        </div>
      </div>
      
      <div class="row">
        <div class="col">
          <div id="logs-container" class="card">
            <div class="card-body" style="max-height: 60vh; overflow-y: auto; font-family: monospace; font-size: 0.9rem;">
              <div id="logs-content">Loading logs...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Set up event listeners
  document.getElementById('refresh-logs').addEventListener('click', refreshLogs);
  
  const categoryCheckboxes = document.querySelectorAll('.category-filter');
  categoryCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', refreshLogs);
  });
  
  document.getElementById('log-level').addEventListener('change', refreshLogs);
  
  const filterInput = document.getElementById('log-filter');
  filterInput.addEventListener('input', refreshLogs);
  
  document.getElementById('log-filter-clear').addEventListener('click', () => {
    filterInput.value = '';
    refreshLogs();
  });
  
  document.getElementById('clear-logs').addEventListener('click', () => {
    document.getElementById('logs-content').innerHTML = '<p class="text-muted">Logs cleared</p>';
  });
  
  document.getElementById('save-logs').addEventListener('click', saveLogs);
  
  // Initial load
  refreshLogs();
}

// Refresh logs with current filters
function refreshLogs() {
  const logsContent = document.getElementById('logs-content');
  logsContent.innerHTML = '<p class="text-center">Loading logs...</p>';
  
  // Get filter values
  const selectedCategories = Array.from(document.querySelectorAll('.category-filter:checked')).map(cb => cb.value);
  const logLevel = document.getElementById('log-level').value;
  const filterText = document.getElementById('log-filter').value;
  
  // Fetch logs from backend
  eel.get_log_entries(logLevel, selectedCategories, filterText)().then(logs => {
    if (!logs || logs.length === 0) {
      logsContent.innerHTML = '<p class="text-muted">No logs found matching the current filters</p>';
      return;
    }
    
    // Format and display logs
    const logHtml = logs.map((log, index) => {
      // Get appropriate color for log level
      let levelClass = '';
      switch (log.level) {
        case 'critical':
        case 'error':
          levelClass = 'text-danger';
          break;
        case 'warning':
          levelClass = 'text-warning';
          break;
        case 'info':
          levelClass = 'text-info';
          break;
        case 'debug':
          levelClass = 'text-secondary';
          break;
        default:
          levelClass = 'text-muted';
      }
      
      // Create log entry HTML
      return `
        <div class="log-entry mb-1" data-index="${index}">
          <span class="log-timestamp text-muted">${log.timestamp}</span>
          <span class="log-category badge bg-dark">${log.category}</span>
          <span class="log-level ${levelClass}">[${log.level.toUpperCase()}]</span>
          <span class="log-message">${escapeHtml(log.message)}</span>
          ${log.details ? 
            `<div class="log-details text-secondary small ms-5 mt-1">Details: ${escapeHtml(log.details)}</div>` : ''}
        </div>
      `;
    }).join('');
    
    logsContent.innerHTML = logHtml;
    
    // Scroll to bottom
    const logsContainer = document.getElementById('logs-container');
    logsContainer.scrollTop = logsContainer.scrollHeight;
  }).catch(error => {
    console.error('Error fetching logs:', error);
    logsContent.innerHTML = `<p class="text-danger">Error loading logs: ${error.message || 'Unknown error'}</p>`;
  });
}

// Save logs to file
function saveLogs() {
  // Get current logs content
  const logsContent = document.getElementById('logs-content').innerText;
  
  // Create blob and download
  const blob = new Blob([logsContent], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = `evrmail_logs_${new Date().toISOString().replace(/:/g, '-')}.txt`;
  document.body.appendChild(a);
  a.click();
  
  // Clean up
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

// Helper function to escape HTML
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Make refresh logs function available globally
window.refreshLogs = refreshLogs; 