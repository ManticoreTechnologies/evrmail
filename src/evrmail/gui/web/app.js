// EvrMail Eel App
document.addEventListener('DOMContentLoaded', initApp);

// Global app state
const appState = {
  currentView: 'loading',
  initialized: false,
  walletReady: false,
  errorState: false
};

// View components
const views = {
  loading: { import: () => import('./components/Loading/loading.js'), element: 'loading-view', fn: 'initLoadingView' },
  home: { import: () => import('./components/Home/home.js'), element: 'home-view', fn: 'initHomeView' },
  inbox: { import: () => import('./components/Inbox/inbox.js'), element: 'inbox-view', fn: 'initInboxView' },
  compose: { import: () => import('./components/Compose/compose.js'), element: 'compose-view', fn: 'initComposeView' },
  wallet: { import: () => import('./components/Wallet/wallet.js'), element: 'wallet-view', fn: 'initWalletView' },
  browser: { import: () => import('./components/Browser/browser.js'), element: 'browser-view', fn: 'initBrowserView' },
  settings: { import: () => import('./components/Settings/settings.js'), element: 'settings-view', fn: 'initSettingsView' },
  logs: { import: () => import('./components/Logs/logs.js'), element: 'logs-view', fn: 'initLogsView' }
};

// Initialize the application
async function initApp() {
  // Create app container divs for all views
  const appContainer = document.getElementById('app-container');
  Object.keys(views).forEach(viewName => {
    const viewDiv = document.createElement('div');
    viewDiv.id = views[viewName].element;
    viewDiv.className = 'view';
    viewDiv.style.display = 'none';
    appContainer.appendChild(viewDiv);
  });
  
  // Show loading view first
  document.getElementById('loading-view').style.display = 'block';
  const loadingMod = await views.loading.import();
  if (loadingMod && typeof loadingMod[views.loading.fn] === 'function') {
    await loadingMod[views.loading.fn]();
  }
  
  // Dynamically import and initialize other views (except loading, home)
  for (const viewName of Object.keys(views)) {
    if (viewName !== 'loading' && viewName !== 'home') {
      try {
        const mod = await views[viewName].import();
        if (mod && typeof mod[views[viewName].fn] === 'function') {
          await mod[views[viewName].fn]();
        }
      } catch (e) {
        console.error(`Error initializing ${viewName} view:`, e);
      }
    }
  }
  
  // Initialize Home view as well
  const homeMod = await views.home.import();
  if (homeMod && typeof homeMod[views.home.fn] === 'function') {
    await homeMod[views.home.fn]();
  }
  
  // Set up navigation
  setupNavigation();
  
  // Set a maximum time before forcing transition to home
  setTimeout(() => {
    if (appState.currentView === 'loading') {
      console.log("Forcing transition to home view after timeout");
      showView('home');
    }
  }, 8000);
  
  // Check daemon status
  checkDaemonStatus();
}

// Set up navigation between views
function setupNavigation() {
  // Wait for navbar to be available
  setTimeout(() => {
    const navLinks = document.querySelectorAll('#nav-items a.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
  }, 100);
}

// Handle navigation
function handleNavigation(event) {
  event.preventDefault();
  
  const targetView = event.currentTarget.dataset.view;
  if (!targetView) return;
  
  console.log(`Navigation requested to: ${targetView}`);
  
  // Update active class
  document.querySelectorAll('#nav-items a.nav-link').forEach(link => {
    link.classList.remove('active');
  });
  event.currentTarget.classList.add('active');
  
  // Show the requested view
  showView(targetView);
}

// Show a specific view
function showView(viewName) {
  if (!views[viewName]) {
    console.error(`View '${viewName}' does not exist`);
    return;
  }
  
  // Skip if already showing this view
  if (appState.currentView === viewName) return;
  
  // Hide all views
  Object.keys(views).forEach(name => {
    document.getElementById(views[name].element).style.display = 'none';
  });
  
  // Show selected view
  const viewElement = document.getElementById(views[viewName].element);
  viewElement.style.display = 'block';
  
  // Special handling for browser view to ensure it takes up full content area (not covering sidebar)
  if (viewName === 'browser') {
    // Use relative positioning to stay within the main content flow
    viewElement.style.position = 'relative';
    viewElement.style.height = '100%';
    viewElement.style.overflow = 'hidden';
  }
  
  // Update current view
  appState.currentView = viewName;
  
  // Special handling for certain views
  switch (viewName) {
    case 'inbox':
      // Reload messages when navigating to inbox
      if (typeof refreshInbox === 'function') {
        refreshInbox();
      }
      break;
    case 'wallet':
      // Refresh wallet data
      if (typeof refreshWallet === 'function') {
        refreshWallet();
      }
      break;
    case 'logs':
      // Refresh logs
      if (typeof refreshLogs === 'function') {
        refreshLogs();
      }
      break;
  }
  
  // Update URL hash for navigation
  window.location.hash = viewName;
}

// Check daemon status and initialize app
function checkDaemonStatus() {
  // Start a timeout to force-continue after 5 seconds if daemon check hangs
  const timeout = setTimeout(() => {
    console.log("Timeout reached - forcing application startup");
    initializeApp();
  }, 5000);
  
  // Show progress updates
  updateLoadingStatus("Connecting to daemon...", 30);
  
  // Check daemon status
  eel.check_daemon_status()().then(status => {
    clearTimeout(timeout); // Clear the timeout since we got a response
    
    if (status.running) {
      console.log("Daemon status check successful:", status);
      updateLoadingStatus("Daemon running, loading application...", 60);
      initializeApp();
    } else {
      console.log("Daemon not running:", status);
      // If daemon is starting but not ready yet, poll until ready
      if (status.status === "starting") {
        updateLoadingStatus("Daemon starting, please wait...", 40);
        // Poll again in 1 second instead of 2
        setTimeout(pollDaemonStatus, 1000);
      } else {
        showDaemonError("Daemon not running. Please restart the application.");
      }
    }
  }).catch(error => {
    clearTimeout(timeout); // Clear the timeout on error
    console.error("Error checking daemon status:", error);
    // Try to start anyway
    initializeApp();
  });
}

// Poll daemon status until ready
function pollDaemonStatus() {
  eel.check_daemon_status()().then(status => {
    if (status.running && status.status === "ready") {
      updateLoadingStatus("Daemon ready, loading application...", 60);
      initializeApp();
    } else if (status.running) {
      updateLoadingStatus("Daemon starting, please wait...", 50);
      // Continue polling with shorter interval
      setTimeout(pollDaemonStatus, 1000);
    } else {
      showDaemonError("Daemon failed to start. Please restart the application.");
    }
  }).catch(error => {
    console.error("Error checking daemon status during polling:", error);
    // Try to start anyway after error
    initializeApp();
  });
}

// Initialize the application after daemon check
function initializeApp() {
  // Show loading message
  updateLoadingStatus("Loading application data...", 70);
  
  try {
    // Preload application data
    eel.preload_app_data()().then(result => {
      updateLoadingStatus("Application data loaded, preparing UI...", 90);
      
      // Hide loading view and show home
      appState.initialized = true;
      appState.walletReady = result.wallet_ready;
      
      // Final loading step - reduced delays
      updateLoadingStatus("Ready!", 100);
      
      // Directly navigate to home instead of waiting
      // Handle initial navigation based on URL hash
      const hash = window.location.hash.substring(1);
      if (hash && views[hash]) {
        showView(hash);
        
        // Update nav active state
        const navLink = document.querySelector(`#nav-items a[data-view="${hash}"]`);
        if (navLink) {
          document.querySelectorAll('#nav-items a.nav-link').forEach(item => item.classList.remove('active'));
          navLink.classList.add('active');
        }
      } else {
        showView('home');
        const homeLink = document.querySelector('#nav-items a[data-view="home"]');
        if (homeLink) homeLink.classList.add('active');
      }
      
      // Update app version in footer
      eel.get_app_version()().then(version => {
        const versionElement = document.getElementById('app-version');
        if (versionElement) {
          versionElement.textContent = `v${version}`;
        }
      }).catch(err => console.error("Error getting app version:", err));
      
    }).catch(error => {
      console.error("Error initializing app:", error);
      // Try to continue anyway with default view
      showView('home');
    });
  } catch (e) {
    console.error("Exception in app initialization:", e);
    // Try to continue anyway with default view
    showView('home');
  }
}

// Update loading status
function updateLoadingStatus(message, progress = null) {
  const statusElement = document.getElementById('loading-status');
  if (statusElement) {
    statusElement.textContent = message;
  }
  
  if (progress !== null) {
    const progressBar = document.getElementById('loading-progress');
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
      progressBar.setAttribute('aria-valuenow', progress);
    }
  }
}

// Show daemon error
function showDaemonError(message) {
  appState.errorState = true;
  const loadingView = document.getElementById('loading-view');
  
  if (loadingView) {
    loadingView.innerHTML = `
      <div class="container text-center">
        <div class="error-container">
          <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Connection Error</h4>
            <p>${message}</p>
            <hr>
            <p class="mb-0">
              <button id="retry-connection" class="btn btn-primary">Retry Connection</button>
            </p>
          </div>
        </div>
      </div>
    `;
    
    // Add retry button handler
    document.getElementById('retry-connection').addEventListener('click', () => {
      // Reload app
      window.location.reload();
    });
  }
}

// Loading view implementation
function initLoadingView() {
  const view = document.getElementById('loading-view');
  
  view.innerHTML = `
    <div class="container text-center">
      <div class="loading-container">
        <img src="evrmail_tray_icon.png" alt="EvrMail Logo" class="loading-logo">
        <h1>EvrMail</h1>
        <p>Secure Email on Everchain</p>
        <div class="progress mb-3">
          <div id="loading-progress" class="progress-bar" role="progressbar" 
               style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
        <p id="loading-status">Loading application...</p>
      </div>
    </div>
  `;
}

// Home view implementation
function initHomeView() {
  const view = document.getElementById('home-view');
  
  view.innerHTML = `
    <div class="container">
      <div class="row mb-4">
        <div class="col">
          <h1>Welcome to EvrMail</h1>
          <p class="lead">Secure, decentralized messaging on the Everchain blockchain</p>
        </div>
      </div>
      
      <div class="row mb-4">
        <div class="col-md-4 mb-3">
          <div class="card h-100">
            <div class="card-body text-center">
              <h5 class="card-title">📬 Messages</h5>
              <p class="card-text">Check your inbox for new messages or compose a new one.</p>
              <div class="mt-3">
                <button class="btn btn-primary me-2" onclick="showView('inbox')">
                  <i class="bi bi-inbox"></i> Inbox
                </button>
                <button class="btn btn-outline-primary" onclick="showView('compose')">
                  <i class="bi bi-pencil"></i> Compose
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-4 mb-3">
          <div class="card h-100">
            <div class="card-body text-center">
              <h5 class="card-title">💰 Wallet</h5>
              <p class="card-text">Manage your EVR assets, send and receive tokens.</p>
              <div class="mt-3">
                <button class="btn btn-primary" onclick="showView('wallet')">
                  <i class="bi bi-wallet2"></i> Open Wallet
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-4 mb-3">
          <div class="card h-100">
            <div class="card-body text-center">
              <h5 class="card-title">🌐 Browser</h5>
              <p class="card-text">Browse EVR domains and decentralized content.</p>
              <div class="mt-3">
                <button class="btn btn-primary" onclick="showView('browser')">
                  <i class="bi bi-globe"></i> Open Browser
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row">
        <div class="col-md-6 mb-3">
          <div class="card">
            <div class="card-header">Network Status</div>
            <div class="card-body">
              <div id="network-status">
                <p class="text-center text-muted">Loading network status...</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-6 mb-3">
          <div class="card">
            <div class="card-header">Quick Stats</div>
            <div class="card-body">
              <div id="quick-stats">
                <p class="text-center text-muted">Loading stats...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Load network status and stats when view is initialized
  loadNetworkStatus();
  loadQuickStats();
}

// Load network status information
function loadNetworkStatus() {
  const statusElement = document.getElementById('network-status');
  
  eel.get_network_status()().then(status => {
    statusElement.innerHTML = `
      <ul class="list-group">
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Connection Status
          <span class="badge bg-${status.connected ? 'success' : 'danger'}">
            ${status.connected ? 'Connected' : 'Disconnected'}
          </span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Network
          <span>${status.network}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Peers
          <span>${status.peers}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Blockchain Height
          <span>${status.height.toLocaleString()}</span>
        </li>
      </ul>
    `;
  }).catch(error => {
    statusElement.innerHTML = `
      <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle-fill"></i> Error loading network status
      </div>
    `;
    console.error('Error loading network status:', error);
  });
}

// Load quick stats
function loadQuickStats() {
  const statsElement = document.getElementById('quick-stats');
  
  Promise.all([
    eel.get_message_stats()(),
    eel.get_wallet_balances()()
  ]).then(([messageStats, walletBalances]) => {
    statsElement.innerHTML = `
      <ul class="list-group">
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Unread Messages
          <span class="badge bg-primary">${messageStats.unread}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Total Messages
          <span>${messageStats.total}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          EVR Balance
          <span>${(walletBalances.total_evr || 0).toFixed(2)} EVR</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          Message Assets
          <span>${Object.keys(walletBalances.assets || {}).length}</span>
        </li>
      </ul>
    `;
  }).catch(error => {
    statsElement.innerHTML = `
      <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle-fill"></i> Error loading statistics
      </div>
    `;
    console.error('Error loading stats:', error);
  });
}

// Make showView function available globally
window.showView = showView; 