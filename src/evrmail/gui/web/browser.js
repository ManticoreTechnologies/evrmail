// EvrMail Browser - Fully embedded browser module

// Initialize the browser view with UI elements and event handlers
function initBrowserView() {
    const browserContainer = document.getElementById('browser-view');
    if (!browserContainer) {
        console.error('Browser view container not found');
        return;
    }

    // Set up browser UI elements
    browserContainer.innerHTML = `
        <div class="main-title">
            <div class="logo">🌐</div>
            <h1>EvrMail Browser</h1>
        </div>
        
        <div class="browser-toolbar">
            <div class="url-container">
                <input type="text" id="url-input" placeholder="Enter URL or EVR domain (e.g. example.com or chess.evr)" class="url-input">
                <button id="load-url-btn" class="btn btn-primary">Load</button>
            </div>
            <div class="browser-actions">
                <button id="refresh-btn" class="btn btn-secondary">Refresh</button>
                <button id="back-btn" class="btn btn-secondary">Back</button>
                <button id="open-external-btn" class="btn btn-outline-secondary">Open in System Browser</button>
            </div>
        </div>
        
        <div class="browser-status-bar">
            <span id="browser-status">Ready</span>
            <button id="clear-browser-btn" class="btn btn-sm btn-secondary">Clear</button>
        </div>
        
        <div id="evr-site-info" class="evr-site-info" style="display: none;">
            <div class="site-info-header">
                <span id="evr-site-title">EVR Domain</span>
                <span id="evr-domain-badge" class="domain-badge">EVR</span>
            </div>
            <div id="evr-site-description" class="site-description"></div>
        </div>
        
        <div class="browser-content">
            <div id="loading-indicator">
                <div class="spinner"></div>
                <div>Loading content...</div>
            </div>
            <iframe id="browser-iframe" sandbox="allow-scripts allow-forms allow-same-origin allow-popups" class="hidden"></iframe>
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
    const loadingIndicator = document.getElementById('loading-indicator');
    const clearBrowserBtn = document.getElementById('clear-browser-btn');
    const evrSiteInfo = document.getElementById('evr-site-info');
    const evrSiteTitle = document.getElementById('evr-site-title');
    const evrSiteDescription = document.getElementById('evr-site-description');
    
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
        
        // Hide EVR site info by default
        evrSiteInfo.style.display = 'none';
        
        // Check if it's an EVR domain
        if (url.endsWith('.evr')) {
            // Handle EVR domain differently - call Python function to fetch IPFS content
            eel.navigate_browser(url)(function(result) {
                if (result.success) {
                    if (result.type === 'evr_domain') {
                        // Show EVR site info
                        if (result.title || result.description) {
                            evrSiteInfo.style.display = 'block';
                            evrSiteTitle.textContent = result.title || result.domain || url;
                            evrSiteDescription.textContent = result.description || '';
                        }
                        
                        // Safely display the EVR domain content in the iframe
                        displaySafeContent(result.content, url, true);
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

    // Function to adjust the iframe height based on content
    function adjustIframeHeight() {
        const iframe = document.getElementById('browser-iframe');
        if (!iframe) return;
        
        try {
            // Set initial height
            iframe.style.height = '100%';
            
            // Wait for content to load
            iframe.onload = function() {
                try {
                    // Get the document height
                    const iframeDoc = iframe.contentWindow.document;
                    const docHeight = Math.max(
                        iframeDoc.body.scrollHeight,
                        iframeDoc.documentElement.scrollHeight,
                        iframeDoc.body.offsetHeight,
                        iframeDoc.documentElement.offsetHeight
                    );
                    
                    // Add some padding to ensure we show everything
                    iframe.style.height = (docHeight + 50) + 'px';
                    console.log("Adjusted iframe height to:", docHeight + 50);
                    
                    // Handle links
                    const iframeLinks = iframeDoc.querySelectorAll('a');
                    iframeLinks.forEach(link => {
                        link.addEventListener('click', (e) => {
                            const href = link.getAttribute('href');
                            if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                                e.preventDefault();
                                navigateTo(href);
                            }
                        });
                    });
                } catch (err) {
                    console.error("Error adjusting iframe height:", err);
                    // Set a fallback height if we can't measure the content
                    iframe.style.height = '800px';
                }
            };
        } catch (error) {
            console.error("Failed to adjust iframe height:", error);
            iframe.style.height = '100%';
        }
    }

    // Function to safely display content in the browser iframe
    function displaySafeContent(content, url, isEvrDomain = false) {
        console.log("Displaying safe content for:", url);
        try {
            const iframe = document.getElementById('browser-iframe');
            if (!iframe) {
                console.error("Browser iframe not found");
                return;
            }

            // Clear any previous content
            iframe.removeAttribute('srcdoc');
            
            // Get the iframe document
            const iframeDoc = iframe.contentWindow.document;
            
            // Clear previous content
            iframeDoc.open();
            
            // Create base URL for relative links
            let baseUrl = '';
            if (url.endsWith('.evr')) {
                // For EVR domains, we'll use ipfs.io as base 
                // (the actual base tag is added server-side in navigate_browser)
                const theme = isDarkMode() ? 'dark' : 'light';
                
                // Write the content with appropriate styling
                iframeDoc.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                                line-height: 1.6;
                                color: ${theme === 'dark' ? '#e1e1e1' : '#333'};
                                background-color: ${theme === 'dark' ? '#222' : '#fff'};
                                padding: 20px;
                                margin: 0;
                            }
                            a {
                                color: ${theme === 'dark' ? '#61dafb' : '#0366d6'};
                            }
                            img {
                                max-width: 100%;
                                height: auto;
                            }
                            pre, code {
                                background-color: ${theme === 'dark' ? '#333' : '#f6f8fa'};
                                border-radius: 3px;
                                padding: 2px 5px;
                            }
                        </style>
                    </head>
                    <body>${content}</body>
                    </html>
                `);
            } else {
                // For regular web content
                iframeDoc.write(content);
            }
            
            // Close the document
            iframeDoc.close();
            
            // Adjust iframe height based on content
            adjustIframeHeight();
            
            // Update UI
            updateStatus(`Loaded: ${url}`);
        } catch (error) {
            console.error("Error displaying content:", error);
            showMessage("Error displaying content: " + error.message, "error");
        }
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
                    <div style="margin-top: 20px;">
                        <p>Try these EVR domains:</p>
                        <ul style="list-style: none; padding: 0;">
                            <li><a href="#" onclick="parent.postMessage({type: 'loadUrl', url: 'search.evr'}, '*')" style="color: #00e0b6; text-decoration: none;">search.evr</a></li>
                            <li><a href="#" onclick="parent.postMessage({type: 'loadUrl', url: 'chess.evr'}, '*')" style="color: #00e0b6; text-decoration: none;">chess.evr</a></li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
        `;
        urlInput.value = '';
        evrSiteInfo.style.display = 'none';
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

    // Function to check if dark mode is enabled
    function isDarkMode() {
        // Default to dark mode if we can't determine
        return true;
    }
    
    // Function to handle navigation within the iframe
    function navigateTo(href) {
        // For relative links, combine with current URL
        const currentUrl = urlInput.value.trim();
        let targetUrl = href;
        
        if (!href.match(/^(https?:\/\/|.*\.evr)/i)) {
            // It's a relative URL
            const urlBase = currentUrl.split('/').slice(0, -1).join('/');
            targetUrl = href.startsWith('/') ? 
                currentUrl.split('/')[0] + '//' + currentUrl.split('/')[2] + href : 
                urlBase + '/' + href;
        }
        
        // Navigate to the URL
        loadUrl(targetUrl);
    }
    
    // Function to show message (used for error handling)
    function showMessage(message, type) {
        console.error(message);
        updateStatus(message, type === "error");
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
    
    // Listen for messages from the iframe
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'loadUrl') {
            loadUrl(event.data.url);
        }
    });

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