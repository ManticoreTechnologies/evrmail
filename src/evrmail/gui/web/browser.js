// EvrMail Browser - Fully embedded browser module

// Initialize the browser view with UI elements and event handlers
function initBrowserView() {
    const browserContainer = document.getElementById('browser-container');
    if (!browserContainer) return;

    // Set up browser UI elements
    browserContainer.innerHTML = `
        <div class="browser-toolbar">
            <div class="url-container">
                <input type="text" id="url-input" placeholder="Enter URL or EVR domain (e.g. example.com or chess.evr)" class="url-input">
                <button id="load-url-btn" class="btn btn-primary"><i class="fas fa-arrow-right"></i> Load</button>
            </div>
            <div class="browser-actions">
                <button id="refresh-btn" class="btn btn-secondary"><i class="fas fa-sync-alt"></i></button>
                <button id="back-btn" class="btn btn-secondary"><i class="fas fa-arrow-left"></i></button>
                <button id="open-external-btn" class="btn btn-outline-secondary"><i class="fas fa-external-link-alt"></i> Open in System Browser</button>
            </div>
        </div>
        <div class="browser-status-bar">
            <span id="browser-status">Ready</span>
            <button id="clear-browser-btn" class="btn btn-sm btn-secondary">Clear</button>
        </div>
        <div class="browser-content">
            <div id="loading-indicator">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <div>Loading content...</div>
            </div>
            <iframe id="browser-iframe" sandbox="allow-scripts allow-forms allow-same-origin allow-popups" class="hidden"></iframe>
            <div id="browser-content-html"></div>
        </div>
    `;

    // Get references to all required elements
    const urlInput = document.getElementById('url-input');
    const loadUrlBtn = document.getElementById('load-url-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const backBtn = document.getElementById('back-btn');
    const openExternalBtn = document.getElementById('open-external-btn');
    const browserStatus = document.getElementById('browser-status');
    const browserIframe = document.getElementById('browser-iframe');
    const browserContentHtml = document.getElementById('browser-content-html');
    const loadingIndicator = document.getElementById('loading-indicator');
    const clearBrowserBtn = document.getElementById('clear-browser-btn');
    
    // Store browser history
    const browserHistory = [];
    let currentHistoryIndex = -1;

    // Function to update browser status
    function updateStatus(message, isError = false) {
        browserStatus.textContent = message;
        browserStatus.className = isError ? 'status-error' : 'status-normal';
    }

    // Function to show loading state
    function showLoading(isLoading) {
        loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        if (!isLoading) {
            browserIframe.classList.remove('hidden');
        }
    }

    // Function to load a URL in the embedded browser
    function loadUrl(url = '') {
        if (!url) {
            url = urlInput.value.trim();
        }
        
        if (!url) {
            updateStatus('Please enter a URL', true);
            return;
        }

        // Update UI
        urlInput.value = url;
        showLoading(true);
        updateStatus(`Loading: ${url}`);
        
        // Check if it's an EVR domain
        if (url.endsWith('.evr')) {
            // Handle EVR domain differently - call Python function to fetch IPFS content
            eel.navigate_browser(url)(function(result) {
                if (result.success) {
                    if (result.type === 'evr_domain') {
                        // Safely display the EVR domain content in the iframe
                        displaySafeContent(result.content, url);
                        // Add to history
                        addToHistory(url);
                    } else {
                        updateStatus('Error: Unexpected result type', true);
                    }
                } else {
                    updateStatus(`Error: ${result.error}`, true);
                    displayError(url, result.error);
                }
                showLoading(false);
            });
        } else {
            // Handle regular URLs by proxying through a Python function
            // This avoids CORS issues and provides a security layer
            
            // Add http:// if missing
            if (!/^https?:\/\//i.test(url)) {
                url = 'https://' + url;
                urlInput.value = url;
            }
            
            eel.navigate_browser(url)(function(result) {
                if (result.success) {
                    // Display the content in the iframe
                    displaySafeContent(result.content, url);
                    // Add to history
                    addToHistory(url);
                } else {
                    updateStatus(`Error: ${result.error}`, true);
                    displayError(url, result.error);
                }
                showLoading(false);
            });
        }
    }
    
    // Function to add a URL to history
    function addToHistory(url) {
        // Remove forward history if we're not at the end
        if (currentHistoryIndex < browserHistory.length - 1) {
            browserHistory.splice(currentHistoryIndex + 1);
        }
        
        // Add new URL to history
        browserHistory.push(url);
        currentHistoryIndex = browserHistory.length - 1;
        
        // Update back button state
        backBtn.disabled = currentHistoryIndex <= 0;
    }
    
    // Function to go back in history
    function goBack() {
        if (currentHistoryIndex > 0) {
            currentHistoryIndex--;
            loadUrl(browserHistory[currentHistoryIndex]);
        }
    }

    // Function to safely display content in the browser iframe
    function displaySafeContent(content, url) {
        // Escape special characters in content to prevent XSS
        const safeContent = escapeHtml(content);
        
        // Create the srcdoc with a base tag to resolve relative URLs
        const baseUrl = new URL(url).origin;
        const srcdoc = `
            <!DOCTYPE html>
            <html>
            <head>
                <base href="${escapeHtml(baseUrl)}/">
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>EvrMail Browser</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        color: #333; 
                        line-height: 1.6;
                    }
                    a { color: #3ea6ff; }
                    img { max-width: 100%; height: auto; }
                </style>
            </head>
            <body>${content}</body>
            </html>
        `;
        
        // Set the iframe content
        browserIframe.srcdoc = srcdoc;
        
        // Update UI
        updateStatus(`Loaded: ${url}`);
    }

    // Function to display error content when loading fails
    function displayError(url, error) {
        // Show a user-friendly error page
        const errorHtml = `
            <div class="browser-error">
                <div class="error-icon">⚠️</div>
                <h2>Error Loading Page</h2>
                <p>Could not load URL: <strong>${escapeHtml(url)}</strong></p>
                <p class="error-message">${escapeHtml(error)}</p>
                <button id="retry-button" class="btn btn-primary">Try Again</button>
            </div>
        `;
        
        // Set the iframe content with the error page
        browserIframe.srcdoc = errorHtml;
        
        // Add event listener for retry button after iframe loads
        browserIframe.onload = function() {
            try {
                const retryButton = browserIframe.contentDocument.getElementById('retry-button');
                if (retryButton) {
                    retryButton.addEventListener('click', function() {
                        loadUrl(url);
                    });
                }
            } catch (e) {
                console.error('Error accessing iframe content:', e);
            }
        };
    }

    // Function to handle "Open in System Browser" button
    function openInSystemBrowser() {
        const url = urlInput.value.trim();
        if (!url) {
            updateStatus('No URL to open', true);
            return;
        }
        
        // Call Python function to open URL in system browser
        eel.open_in_system_browser(url)();
        updateStatus(`Opened in system browser: ${url}`);
    }

    // Function to clear the browser content
    function clearBrowser() {
        browserIframe.srcdoc = `
            <html>
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #121212; color: #ccc; font-family: Arial;">
                <div style="text-align: center;">
                    <h2 style="color: #3ea6ff;">EvrMail Browser</h2>
                    <p>Enter a URL above to start browsing</p>
                </div>
            </body>
            </html>
        `;
        urlInput.value = '';
        updateStatus('Browser cleared');
    }

    // Helper function to escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Event listeners
    loadUrlBtn.addEventListener('click', () => loadUrl());
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadUrl();
    });
    refreshBtn.addEventListener('click', () => loadUrl(urlInput.value.trim()));
    backBtn.addEventListener('click', goBack);
    openExternalBtn.addEventListener('click', openInSystemBrowser);
    clearBrowserBtn.addEventListener('click', clearBrowser);

    // Initialize browser with empty state
    clearBrowser();
    backBtn.disabled = true;
}

// Initialize browser when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the browser view when the tab is loaded
    initBrowserView();
});

// Make initBrowserView available globally
window.initBrowserView = initBrowserView;