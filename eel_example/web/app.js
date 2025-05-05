// Main application script for EvrMail
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the application
  initializeApp();
});

// Global variables
let currentView = 'loading';
let daemonReady = false;

// Initialize the application
function initializeApp() {
  // Set up navigation
  setupNavigation();
  
  // Add event listener for log updates
  window.addEventListener('log-update', handleLogUpdate);
  
  // Check daemon status regularly
  checkDaemonStatus();
}

// Set up navigation event listeners
function setupNavigation() {
  const navLinks = document.querySelectorAll('#menu .nav-link');
  
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const view = this.getAttribute('data-view');
      if (view) {
        setActiveNavLink(this);
        showView(view);
      }
    });
  });
}

// Set active navigation link
function setActiveNavLink(activeLink) {
  const navLinks = document.querySelectorAll('#menu .nav-link');
  navLinks.forEach(link => {
    link.classList.remove('active');
  });
  activeLink.classList.add('active');
}

// Show the selected view
function showView(viewName) {
  if (viewName === currentView) return;
  
  // If daemon is not ready and trying to navigate away from loading, return
  if (!daemonReady && viewName !== 'loading') {
    // Find the inbox nav link and click it once daemon is ready
    const checkInterval = setInterval(() => {
      if (daemonReady) {
        clearInterval(checkInterval);
        const navLink = document.querySelector(`[data-view="${viewName}"]`);
        if (navLink) navLink.click();
      }
    }, 500);
    return;
  }
  
  // Hide all views
  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.add('d-none');
  });
  
  // Show loading view if daemon is not ready yet
  if (!daemonReady && viewName !== 'loading') {
    document.getElementById('loading-view').classList.remove('d-none');
    return;
  }
  
  // Show selected view
  const viewElement = document.getElementById(`${viewName}-view`);
  if (viewElement) {
    viewElement.classList.remove('d-none');
    currentView = viewName;
    
    // Load view content if it hasn't been loaded yet
    if (viewElement.getAttribute('data-loaded') !== 'true') {
      loadViewContent(viewName);
      viewElement.setAttribute('data-loaded', 'true');
    }
  }
}

// Load view content
function loadViewContent(viewName) {
  switch (viewName) {
    case 'inbox':
      loadInboxView();
      break;
    case 'compose':
      loadComposeView();
      break;
    case 'wallet':
      loadWalletView();
      break;
    case 'browser':
      loadBrowserView();
      break;
    case 'settings':
      loadSettingsView();
      break;
    case 'logs':
      loadLogsView();
      break;
  }
}

// Check daemon status
function checkDaemonStatus() {
  // Poll for daemon startup completion
  const checkInterval = setInterval(() => {
    eel.get_log_entries('info')().then(entries => {
      const readyEntries = entries.filter(entry => 
        entry.message.includes('Daemon listening for transactions') || 
        entry.message.includes('Reloading known addresses') ||
        entry.message.includes('Block processed with')
      );
      
      if (readyEntries.length > 0) {
        daemonReady = true;
        clearInterval(checkInterval);
        // Automatically navigate to inbox
        showView('inbox');
        const inboxLink = document.querySelector('[data-view="inbox"]');
        if (inboxLink) setActiveNavLink(inboxLink);
      }
    });
  }, 1000);
  
  // Display log entries in the loading view
  displayLoadingLogs();
}

// Display log entries in the loading view
function displayLoadingLogs() {
  const logsContainer = document.getElementById('loading-logs');
  
  // Update log display every second
  setInterval(() => {
    eel.get_log_entries()().then(entries => {
      logsContainer.innerHTML = '';
      entries.slice(-10).forEach(entry => {
        const logLine = document.createElement('div');
        logLine.className = 'log-line';
        logLine.innerHTML = `<span class="text-muted">[${entry.timestamp}]</span> <span class="text-${getLogLevelColor(entry.level)}">[${entry.category}]</span> ${entry.message}`;
        logsContainer.appendChild(logLine);
      });
      
      // Scroll to bottom
      logsContainer.scrollTop = logsContainer.scrollHeight;
    });
  }, 1000);
}

// Get color class for log level
function getLogLevelColor(level) {
  switch (level) {
    case 'critical': return 'danger';
    case 'error': return 'danger';
    case 'warning': return 'warning';
    case 'info': return 'info';
    case 'debug': return 'secondary';
    default: return 'light';
  }
}

// Handle log update event
function handleLogUpdate(e) {
  // This would be used for real-time log updates if needed
}

// Load view implementations
function loadInboxView() {
  const view = document.getElementById('inbox-view');
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">📬 EvrMail Unified Inbox</h1>
      <div class="card mb-4">
        <div class="card-body">
          <div class="message-list" id="message-list">
            <p class="text-center text-muted">Loading messages...</p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">Message Content</div>
        <div class="card-body">
          <div class="message-content" id="message-content">
            <p class="text-muted">Select a message to view its content</p>
          </div>
        </div>
      </div>
      <div class="text-center mt-3">
        <button class="btn btn-primary" id="refresh-inbox">
          <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
      </div>
    </div>
  `;
  
  // Set up refresh button
  document.getElementById('refresh-inbox').addEventListener('click', refreshInbox);
  
  // Initial load
  refreshInbox();
}

// Refresh inbox
function refreshInbox() {
  const messageList = document.getElementById('message-list');
  messageList.innerHTML = '<p class="text-center text-muted">Loading messages...</p>';
  
  Promise.all([
    eel.get_inbox_messages()(),
    eel.get_sent_messages()()
  ]).then(([inboxMessages, sentMessages]) => {
    // Combine messages
    const allMessages = [
      ...inboxMessages.map(msg => ({...msg, icon: 'inbox-fill', iconColor: 'info'})),
      ...sentMessages.map(msg => ({
        ...msg, 
        icon: msg.is_dry_run ? 'flask' : 'send-fill', 
        iconColor: msg.is_dry_run ? 'warning' : 'success'
      }))
    ];
    
    // Display messages
    renderMessages(allMessages);
  });
}

// Render messages in the inbox
function renderMessages(messages) {
  const messageList = document.getElementById('message-list');
  
  if (messages.length === 0) {
    messageList.innerHTML = '<p class="text-center text-muted">No messages found</p>';
    return;
  }
  
  messageList.innerHTML = '';
  
  // Create list
  const list = document.createElement('div');
  list.className = 'list-group';
  
  messages.forEach(message => {
    const listItem = document.createElement('a');
    listItem.href = '#';
    listItem.className = 'list-group-item list-group-item-action';
    listItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between">
        <h5 class="mb-1">
          <i class="bi bi-${message.icon} text-${message.iconColor}"></i>
          ${message.type === 'received' ? 'From: ' + message.from : 'To: ' + message.to}
        </h5>
      </div>
      <p class="mb-1">${message.subject}</p>
    `;
    
    // Click handler
    listItem.addEventListener('click', () => {
      // Make active
      document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
      });
      listItem.classList.add('active');
      
      // Show content
      const contentElement = document.getElementById('message-content');
      let header = message.type === 'received' ? 
        `<h5>📥 From: ${message.from}</h5>` : 
        `<h5>📤 To: ${message.to}</h5>`;
      
      contentElement.innerHTML = `
        ${header}
        <h6>Subject: ${message.subject}</h6>
        <hr>
        <div class="message-body">${message.body}</div>
      `;
    });
    
    list.appendChild(listItem);
  });
  
  messageList.appendChild(list);
}

// Implement other view loading functions (to be added in separate files)
function loadComposeView() {
  // Implementation will be added in compose.js
  const view = document.getElementById('compose-view');
  view.innerHTML = '<p class="text-center">Loading compose view...</p>';
  
  // Load compose view module
  const script = document.createElement('script');
  script.src = 'compose.js';
  script.onload = () => initComposeView();
  document.head.appendChild(script);
}

function loadWalletView() {
  // Implementation will be added in wallet.js
  const view = document.getElementById('wallet-view');
  view.innerHTML = '<p class="text-center">Loading wallet view...</p>';
  
  // Load wallet view module
  const script = document.createElement('script');
  script.src = 'wallet.js';
  script.onload = () => initWalletView();
  document.head.appendChild(script);
}

function loadBrowserView() {
  // Implementation will be added in browser.js
  const view = document.getElementById('browser-view');
  view.innerHTML = '<p class="text-center">Loading browser view...</p>';
  
  // Load browser view module
  const script = document.createElement('script');
  script.src = 'browser.js';
  script.onload = () => initBrowserView();
  document.head.appendChild(script);
}

function loadSettingsView() {
  // Implementation will be added in settings.js
  const view = document.getElementById('settings-view');
  view.innerHTML = '<p class="text-center">Loading settings view...</p>';
  
  // Load settings view module
  const script = document.createElement('script');
  script.src = 'settings.js';
  script.onload = () => initSettingsView();
  document.head.appendChild(script);
}

function loadLogsView() {
  // Implementation will be added in logs.js
  const view = document.getElementById('logs-view');
  view.innerHTML = '<p class="text-center">Loading logs view...</p>';
  
  // Load logs view module
  const script = document.createElement('script');
  script.src = 'logs.js';
  script.onload = () => initLogsView();
  document.head.appendChild(script);
} 