import { loadTemplate } from '../../utils.js';

// Logs view implementation
export async function initLogsView() {
  await loadTemplate('components/Logs/logs.html', 'logs-view');
  
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
export function refreshLogs() {
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