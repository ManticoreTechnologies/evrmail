// Logs view implementation
function initLogsView() {
  const view = document.getElementById('logs-view');
  
  // Create logs viewer
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">📜 EvrMail Logs</h1>
      
      <div class="card mb-3">
        <div class="card-body">
          <div class="row">
            <div class="col-md-12 mb-3">
              <div class="d-flex flex-wrap justify-content-center gap-2">
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="APP" id="cat-app" checked>
                  <label class="form-check-label text-info" for="cat-app">App</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="GUI" id="cat-gui" checked>
                  <label class="form-check-label text-primary" for="cat-gui">GUI</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="DAEMON" id="cat-daemon" checked>
                  <label class="form-check-label text-warning" for="cat-daemon">Daemon</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="WALLET" id="cat-wallet" checked>
                  <label class="form-check-label text-success" for="cat-wallet">Wallet</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="CHAIN" id="cat-chain" checked>
                  <label class="form-check-label text-danger" for="cat-chain">Chain</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="NETWORK" id="cat-network" checked>
                  <label class="form-check-label text-light" for="cat-network">Network</label>
                </div>
                <div class="form-check form-check-inline">
                  <input class="form-check-input" type="checkbox" value="DEBUG" id="cat-debug" checked>
                  <label class="form-check-label text-secondary" for="cat-debug">Debug</label>
                </div>
              </div>
            </div>
          </div>
          
          <div class="row align-items-center">
            <div class="col-md-4 mb-2">
              <div class="input-group">
                <span class="input-group-text">Level</span>
                <select class="form-select" id="log-level">
                  <option value="all">🔍 All Levels</option>
                  <option value="debug">🔍 Debug & Above</option>
                  <option value="info" selected>ℹ️ Info & Above</option>
                  <option value="warning">⚠️ Warnings & Above</option>
                  <option value="error">❌ Errors Only</option>
                  <option value="critical">🔥 Critical Only</option>
                </select>
              </div>
            </div>
            
            <div class="col-md-5 mb-2">
              <div class="input-group">
                <span class="input-group-text">Filter</span>
                <input type="text" class="form-control" id="log-filter" placeholder="Filter logs...">
              </div>
            </div>
            
            <div class="col-md-3 mb-2 d-flex justify-content-end gap-2">
              <button id="clear-logs" class="btn btn-outline-danger">
                <i class="bi bi-trash"></i> Clear
              </button>
              <button id="save-logs" class="btn btn-outline-primary">
                <i class="bi bi-download"></i> Save
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-body p-0">
          <div id="logs-container" class="log-container bg-dark p-3 text-light" style="max-height: 400px; overflow-y: auto; font-family: monospace;">
            <div id="logs-content">Loading logs...</div>
          </div>
        </div>
      </div>
      
      <div id="save-status" class="mt-3 alert d-none" role="alert"></div>
    </div>
  `;
  
  // Set up event listeners
  setupLogControls();
  
  // Load logs initially
  refreshLogs();
  
  // Set up auto-refresh
  setInterval(refreshLogs, 3000);
}

// Set up log filter controls
function setupLogControls() {
  // Category checkboxes
  document.querySelectorAll('[id^="cat-"]').forEach(checkbox => {
    checkbox.addEventListener('change', refreshLogs);
  });
  
  // Log level selector
  document.getElementById('log-level').addEventListener('change', refreshLogs);
  
  // Filter input
  document.getElementById('log-filter').addEventListener('input', refreshLogs);
  
  // Clear logs button
  document.getElementById('clear-logs').addEventListener('click', () => {
    document.getElementById('logs-content').innerHTML = 'Logs cleared';
    // In a real implementation, we would clear the logs in Python too
  });
  
  // Save logs button
  document.getElementById('save-logs').addEventListener('click', saveLogs);
}

// Refresh logs display
function refreshLogs() {
  // Get filter criteria
  const levelFilter = document.getElementById('log-level').value;
  const textFilter = document.getElementById('log-filter').value;
  
  // Get selected categories
  const categoryFilter = Array.from(document.querySelectorAll('[id^="cat-"]:checked'))
    .map(cb => cb.value);
  
  // Get logs with filters
  eel.get_log_entries(levelFilter, categoryFilter, textFilter)().then(entries => {
    const logsContent = document.getElementById('logs-content');
    
    if (entries.length === 0) {
      logsContent.innerHTML = '<p class="text-muted">No logs match the current filter criteria</p>';
      return;
    }
    
    // Update logs display
    logsContent.innerHTML = '';
    
    entries.forEach(entry => {
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      
      // Get category color
      const categoryColors = {
        APP: 'info',
        GUI: 'primary',
        DAEMON: 'warning',
        WALLET: 'success',
        CHAIN: 'danger',
        NETWORK: 'light',
        DEBUG: 'secondary'
      };
      
      // Get level icon and color
      const levelIcons = {
        debug: '🔍',
        info: 'ℹ️',
        warning: '⚠️',
        error: '❌',
        critical: '🔥'
      };
      
      const levelColors = {
        debug: 'secondary',
        info: 'info',
        warning: 'warning',
        error: 'danger',
        critical: 'danger'
      };
      
      const catColor = categoryColors[entry.category] || 'light';
      const levelColor = levelColors[entry.level] || 'light';
      const levelIcon = levelIcons[entry.level] || 'ℹ️';
      
      // Build the log entry HTML
      logEntry.innerHTML = `
        <span class="text-muted">[${entry.timestamp}]</span>
        <span class="text-${levelColor}">${levelIcon}</span>
        <span class="text-${catColor}">[${entry.category}]</span>
        <span>${entry.message}</span>
      `;
      
      // Add expandable details if present
      if (entry.details) {
        const detailsElement = document.createElement('div');
        detailsElement.className = 'log-details ps-4 mt-1 border-start border-secondary';
        detailsElement.style.display = 'none';
        
        // Format details
        if (typeof entry.details === 'object') {
          detailsElement.innerHTML = `<pre class="text-success">${JSON.stringify(entry.details, null, 2)}</pre>`;
        } else {
          detailsElement.textContent = entry.details;
        }
        
        // Make log entry expandable
        logEntry.style.cursor = 'pointer';
        logEntry.addEventListener('click', () => {
          detailsElement.style.display = detailsElement.style.display === 'none' ? 'block' : 'none';
        });
        
        logEntry.appendChild(detailsElement);
      }
      
      logsContent.appendChild(logEntry);
    });
    
    // Scroll to bottom if auto-scroll is enabled
    const logsContainer = document.getElementById('logs-container');
    logsContainer.scrollTop = logsContainer.scrollHeight;
  });
}

// Save logs
function saveLogs() {
  const statusElement = document.getElementById('save-status');
  statusElement.className = 'alert alert-info';
  statusElement.textContent = 'Saving logs would save to a file in a real implementation.';
  statusElement.classList.remove('d-none');
  
  // Hide the status after a few seconds
  setTimeout(() => {
    statusElement.classList.add('d-none');
  }, 3000);
} 