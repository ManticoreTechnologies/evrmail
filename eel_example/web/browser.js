// Browser view implementation
function initBrowserView() {
  const view = document.getElementById('browser-view');
  
  // Create browser UI
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">🌐 EvrMail Browser</h1>
      
      <div class="card mb-3">
        <div class="card-body">
          <div class="input-group mb-3">
            <input type="text" class="form-control" id="url-input" placeholder="🔎 Enter URL or EvrNet domain (e.g. example.com or chess.evr)...">
            <button class="btn btn-primary" id="load-url-btn">
              <i class="bi bi-search"></i> Load
            </button>
          </div>
          
          <div class="d-flex justify-content-center mb-2">
            <button class="btn btn-outline-primary" id="open-external-btn">
              <i class="bi bi-box-arrow-up-right"></i> Open in System Browser
            </button>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span id="browser-status">Ready</span>
          <button class="btn btn-sm btn-outline-secondary" id="refresh-browser-btn">
            <i class="bi bi-arrow-clockwise"></i>
          </button>
        </div>
        <div class="card-body">
          <div id="browser-frame-container" class="border rounded p-2" style="min-height: 400px; background-color: var(--darker-bg);">
            <div id="browser-content" class="text-center p-5">
              <h3 class="text-primary">Enter a URL or EVR domain above to browse</h3>
              <p class="text-muted">Examples: example.com, chess.evr</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Set up event listeners
  const urlInput = document.getElementById('url-input');
  const loadUrlBtn = document.getElementById('load-url-btn');
  const openExternalBtn = document.getElementById('open-external-btn');
  const refreshBrowserBtn = document.getElementById('refresh-browser-btn');
  
  // Load URL button
  loadUrlBtn.addEventListener('click', () => {
    loadUrl(urlInput.value);
  });
  
  // Enter key in URL input
  urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      loadUrl(urlInput.value);
    }
  });
  
  // Open in external browser
  openExternalBtn.addEventListener('click', () => {
    if (urlInput.value) {
      openExternalUrl(urlInput.value);
    }
  });
  
  // Refresh button
  refreshBrowserBtn.addEventListener('click', () => {
    if (urlInput.value) {
      loadUrl(urlInput.value);
    }
  });
}

// Load URL in the browser frame
function loadUrl(url) {
  if (!url) return;
  
  // Update status
  const statusElement = document.getElementById('browser-status');
  statusElement.textContent = `Loading: ${url}`;
  
  const contentContainer = document.getElementById('browser-content');
  contentContainer.innerHTML = `
    <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  `;
  
  // Process URL - check if it's an EVR domain
  if (url.endsWith('.evr')) {
    // Handle EVR domain with simulated content
    eel.navigate_browser(url)().then(result => {
      if (result.success) {
        if (result.type === 'evr_domain') {
          // Create a sandboxed iframe to display the content
          contentContainer.innerHTML = `
            <iframe srcdoc="${escapeHtml(result.content)}" 
                    sandbox="allow-scripts allow-same-origin" 
                    style="width: 100%; height: 400px; border: none;"></iframe>
          `;
          statusElement.textContent = `Loaded EVR domain: ${url}`;
        } else if (result.opened_in_system) {
          contentContainer.innerHTML = `
            <div class="alert alert-info">
              <p>Opening in system browser: ${url}</p>
            </div>
          `;
          statusElement.textContent = `Opened in system browser: ${url}`;
        }
      } else {
        // Show error
        contentContainer.innerHTML = `
          <div class="alert alert-danger">
            <h4>Error Loading Page</h4>
            <p>${result.error || 'Unknown error'}</p>
          </div>
        `;
        statusElement.textContent = `Error loading: ${url}`;
      }
    });
  } else {
    // Regular web URL - open in system browser and show message
    openExternalUrl(url);
    contentContainer.innerHTML = `
      <div class="alert alert-info">
        <p>Opening in system browser: ${url}</p>
      </div>
    `;
    statusElement.textContent = `Opened in system browser: ${url}`;
  }
}

// Open URL in external browser
function openExternalUrl(url) {
  // Ensure URL has http/https prefix
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }
  
  // Use Eel to open URL
  eel.navigate_browser(url)();
}

// Helper function to escape HTML for srcdoc attribute
function escapeHtml(html) {
  const div = document.createElement('div');
  div.textContent = html;
  return div.innerHTML.replace(/"/g, '&quot;');
} 