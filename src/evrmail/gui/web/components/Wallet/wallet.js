import { loadTemplate } from '../../utils.js';

// import walletTemplate from './wallet.html'; // If using a bundler, otherwise use fetch

export async function initWalletView() {
  await loadTemplate('components/Wallet/wallet.html', 'wallet-view');
  // Set up event listeners and any initial logic here
  
  const view = document.getElementById('wallet-view');
  
  // Create wallet UI with tabs
  view.innerHTML = `
    <div class="container">
      <h1 class="mb-4">
        <i class="bi bi-wallet2"></i> Wallet Overview
      </h1>
      
      <ul class="nav nav-tabs" id="walletTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="addresses-tab" data-bs-toggle="tab" data-bs-target="#addresses-content" 
                  type="button" role="tab" aria-controls="addresses-content" aria-selected="true">
            Addresses
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="balances-tab" data-bs-toggle="tab" data-bs-target="#balances-content" 
                  type="button" role="tab" aria-controls="balances-content" aria-selected="false">
            Balances
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="utxos-tab" data-bs-toggle="tab" data-bs-target="#utxos-content" 
                  type="button" role="tab" aria-controls="utxos-content" aria-selected="false">
            UTXOs
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="send-tab" data-bs-toggle="tab" data-bs-target="#send-content" 
                  type="button" role="tab" aria-controls="send-content" aria-selected="false">
            Send
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="receive-tab" data-bs-toggle="tab" data-bs-target="#receive-content" 
                  type="button" role="tab" aria-controls="receive-content" aria-selected="false">
            Receive
          </button>
        </li>
      </ul>
      
      <div class="tab-content p-3 border border-top-0 rounded-bottom" id="walletTabsContent">
        <!-- Addresses Tab -->
        <div class="tab-pane fade show active" id="addresses-content" role="tabpanel" aria-labelledby="addresses-tab">
          <div class="d-flex justify-content-between mb-3">
            <h3>Derived Addresses</h3>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="show-labeled-only">
              <label class="form-check-label" for="show-labeled-only">
                Only show user-labeled addresses
              </label>
            </div>
          </div>
          
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Index</th>
                  <th>Label</th>
                  <th>Address</th>
                  <th>Path</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="address-list">
                <tr>
                  <td colspan="5" class="text-center">Loading addresses...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Balances Tab -->
        <div class="tab-pane fade" id="balances-content" role="tabpanel" aria-labelledby="balances-tab">
          <h3 class="mb-3">Wallet Balances</h3>
          <div id="balances-container">
            <p class="text-center">Loading balances...</p>
          </div>
        </div>
        
        <!-- UTXOs Tab -->
        <div class="tab-pane fade" id="utxos-content" role="tabpanel" aria-labelledby="utxos-tab">
          <h3 class="mb-3">Unspent Transaction Outputs</h3>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>TXID</th>
                  <th>Index</th>
                  <th>Address</th>
                  <th>Asset</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody id="utxo-list">
                <tr>
                  <td colspan="6" class="text-center">Loading UTXOs...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Send Tab -->
        <div class="tab-pane fade" id="send-content" role="tabpanel" aria-labelledby="send-tab">
          <h3 class="mb-3">Send Funds</h3>
          <form id="send-form">
            <div class="mb-3">
              <label for="send-address" class="form-label">Recipient Address</label>
              <input type="text" class="form-control" id="send-address" placeholder="Enter recipient address" required>
            </div>
            
            <div class="mb-3">
              <label for="send-amount" class="form-label">Amount</label>
              <div class="input-group">
                <input type="number" step="0.00000001" min="0.00000001" class="form-control" id="send-amount" placeholder="0.0" required>
                <span class="input-group-text">EVR</span>
              </div>
            </div>
            
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="send-dry-run">
              <label class="form-check-label" for="send-dry-run">Dry run (simulate, don't broadcast)</label>
            </div>
            
            <div id="send-status" class="alert d-none" role="alert"></div>
            
            <button type="submit" class="btn btn-primary">
              <i class="bi bi-send"></i> Send
            </button>
          </form>
        </div>
        
        <!-- Receive Tab -->
        <div class="tab-pane fade" id="receive-content" role="tabpanel" aria-labelledby="receive-tab">
          <h3 class="mb-3">Generate Receiving Address</h3>
          <form id="receive-form">
            <div class="mb-3">
              <label for="wallet-select" class="form-label">Wallet</label>
              <select class="form-select" id="wallet-select">
                <option value="default" selected>Default Wallet</option>
              </select>
            </div>
            
            <div class="mb-3">
              <label for="address-label" class="form-label">Address Label (optional)</label>
              <input type="text" class="form-control" id="address-label" placeholder="Enter a friendly name for this address">
            </div>
            
            <div id="receive-status" class="alert d-none" role="alert"></div>
            
            <button type="submit" class="btn btn-primary mb-3">
              <i class="bi bi-plus-circle"></i> Generate Address
            </button>
          </form>
          
          <div id="address-result" class="d-none card mt-4">
            <div class="card-body text-center">
              <h5 class="card-title">New Address</h5>
              <div id="qr-code" class="mx-auto mb-3" style="width:150px; height:150px;"></div>
              <p class="card-text mb-0"><strong>Address:</strong></p>
              <p id="new-address" class="font-monospace bg-light p-2 rounded">(address will appear here)</p>
              <button id="copy-address" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-clipboard"></i> Copy Address
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Initialize tabs
  setupTabs();
  
  // Set up event listeners
  setupEventListeners();
  
  // Load initial data
  refreshWallet();
}

// Set up Bootstrap tabs
function setupTabs() {
  // This ensures Bootstrap tab functionality works
  const triggerTabList = [].slice.call(document.querySelectorAll('#walletTabs button'));
  triggerTabList.forEach(function(triggerEl) {
    triggerEl.addEventListener('click', function(event) {
      event.preventDefault();
      const tabTrigger = new bootstrap.Tab(triggerEl);
      tabTrigger.show();
    });
  });
}

// Set up form event listeners
function setupEventListeners() {
  // Set up addresses tab
  document.getElementById('show-labeled-only').addEventListener('change', function() {
    loadAddresses(this.checked);
  });
  
  // Add diagnostic button
  const addressesContent = document.getElementById('addresses-content');
  const diagnosticButton = document.createElement('button');
  diagnosticButton.id = 'diagnostic-button';
  diagnosticButton.className = 'btn btn-sm btn-outline-secondary mt-3';
  diagnosticButton.innerHTML = '<i class="bi bi-tools"></i> Diagnostic Info';
  diagnosticButton.addEventListener('click', showWalletDiagnostics);
  addressesContent.appendChild(diagnosticButton);
  
  // Set up send form submission
  document.getElementById('send-form').addEventListener('submit', function(e) {
    e.preventDefault();
    sendFunds();
  });
  
  // Set up receive form submission
  document.getElementById('receive-form').addEventListener('submit', function(e) {
    e.preventDefault();
    generateAddress();
  });
  
  // Set up copy address button
  document.getElementById('copy-address').addEventListener('click', function() {
    const address = document.getElementById('new-address').textContent;
    navigator.clipboard.writeText(address).then(() => {
      // Show tooltip
      this.textContent = '✓ Copied!';
      setTimeout(() => {
        this.innerHTML = '<i class="bi bi-clipboard"></i> Copy Address';
      }, 2000);
    });
  });
}

// Show wallet diagnostics
function showWalletDiagnostics() {
  const addressList = document.getElementById('address-list');
  addressList.innerHTML = '<tr><td colspan="5" class="text-center">Loading diagnostic information...</td></tr>';
  
  // Get diagnostic information
  eel.get_wallet_info()().then(info => {
    let html = '<tr><td colspan="5">';
    html += '<div class="alert alert-info">';
    html += '<h5>Wallet Diagnostic Information</h5>';
    html += '<pre>' + JSON.stringify(info, null, 2) + '</pre>';
    html += '</div>';
    
    // Add a button to reload addresses
    html += '<button id="reload-addresses" class="btn btn-primary">Reload Addresses</button>';
    html += '</td></tr>';
    
    addressList.innerHTML = html;
    
    // Add click handler for reload button
    document.getElementById('reload-addresses').addEventListener('click', () => {
      loadAddresses(document.getElementById('show-labeled-only').checked);
    });
  }).catch(error => {
    console.error('Error getting wallet diagnostics:', error);
    addressList.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error: ${error.message || 'Unknown error'}</td></tr>`;
  });
}

// Refresh all wallet data
function refreshWallet() {
  // Load wallet data
  loadAddresses();
  loadBalances();
  loadUTXOs();
  loadWalletList();
}

// Load wallet addresses
function loadAddresses(labeledOnly = false) {
  console.log('Loading addresses...');
  
  const addressList = document.getElementById('address-list');
  addressList.innerHTML = '<tr><td colspan="5" class="text-center">Loading addresses...</td></tr>';
  
  // Fetch addresses from backend
  eel.get_wallet_addresses()().then(addresses => {
    console.log('Received addresses:', addresses);
    
    if (!addresses || addresses.length === 0) {
      addressList.innerHTML = '<tr><td colspan="5" class="text-center">No addresses found</td></tr>';
      return;
    }
    
    // Filter addresses if needed - don't show auto-generated labels (address_XXXX)
    let displayAddresses = [...addresses];
    if (labeledOnly) {
      displayAddresses = addresses.filter(addr => {
        const label = addr.label || '';
        return label.trim() !== '' && !label.startsWith('address_');
      });
      
      if (displayAddresses.length === 0) {
        addressList.innerHTML = '<tr><td colspan="5" class="text-center">No labeled addresses found. Uncheck "Only show user-labeled addresses" to see all addresses.</td></tr>';
        return;
      }
    }
    
    // Render addresses
    addressList.innerHTML = displayAddresses.map(addr => {
      // Format the label properly
      let displayLabel = 'No label';
      if (addr.label) {
        displayLabel = addr.label.startsWith('address_') ? 'No label' : addr.label;
      }
      
      return `
        <tr>
          <td>${addr.index !== undefined ? addr.index : 'N/A'}</td>
          <td>${displayLabel !== 'No label' ? displayLabel : '<em>No label</em>'}</td>
          <td class="font-monospace small">${addr.address || 'N/A'}</td>
          <td class="font-monospace small">${addr.path || 'Unknown'}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary copy-addr" data-address="${addr.address}">
              <i class="bi bi-clipboard"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
    
    // Add click handlers for copy buttons
    document.querySelectorAll('.copy-addr').forEach(btn => {
      btn.addEventListener('click', function() {
        const address = this.getAttribute('data-address');
        navigator.clipboard.writeText(address).then(() => {
          // Change button text temporarily
          const originalHtml = this.innerHTML;
          this.innerHTML = '<i class="bi bi-check"></i>';
          setTimeout(() => {
            this.innerHTML = originalHtml;
          }, 1000);
        });
      });
    });
  }).catch(error => {
    console.error('Error loading addresses:', error);
    addressList.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading addresses: ${error.message || 'Unknown error'}</td></tr>`;
  });
}

// Load wallet balances
function loadBalances() {
  const balancesContainer = document.getElementById('balances-container');
  balancesContainer.innerHTML = '<p class="text-center">Loading balances...</p>';
  
  eel.get_wallet_balances()().then(balances => {
    if (!balances) {
      balancesContainer.innerHTML = '<p class="text-center">Error loading balances</p>';
      return;
    }
    
    // Build balances display
    let html = `
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">EVR</h5>
        </div>
        <div class="card-body">
          <h3 class="card-title text-success">${balances.total_evr.toFixed(8)} EVR</h3>
          <p class="card-text">Total across all addresses</p>
        </div>
      </div>
    `;
    
    // Add EVR balances by address
    if (Object.keys(balances.evr).length > 0) {
      html += `
        <div class="card mb-4">
          <div class="card-header">EVR by Address</div>
          <div class="list-group list-group-flush">
      `;
      
      for (const [address, amount] of Object.entries(balances.evr)) {
        html += `
          <div class="list-group-item">
            <div class="d-flex justify-content-between align-items-center">
              <span class="font-monospace text-truncate" style="max-width: 60%;">${address}</span>
              <span>${amount.toFixed(8)} EVR</span>
            </div>
          </div>
        `;
      }
      
      html += `
          </div>
        </div>
      `;
    }
    
    // Add assets if any
    if (Object.keys(balances.assets).length > 0) {
      html += '<h4 class="mt-4">Assets</h4>';
      
      for (const [assetName, addresses] of Object.entries(balances.assets)) {
        const totalAsset = Object.values(addresses).reduce((sum, amount) => sum + amount, 0);
        
        html += `
          <div class="card mb-3">
            <div class="card-header">
              <h5 class="mb-0">${assetName}</h5>
            </div>
            <div class="card-body">
              <h3 class="card-title text-primary">${totalAsset.toFixed(8)}</h3>
              <p class="card-text">Total across all addresses</p>
            </div>
            <div class="list-group list-group-flush">
        `;
        
        for (const [address, amount] of Object.entries(addresses)) {
          html += `
            <div class="list-group-item">
              <div class="d-flex justify-content-between align-items-center">
                <span class="font-monospace text-truncate" style="max-width: 60%;">${address}</span>
                <span>${amount.toFixed(8)}</span>
              </div>
            </div>
          `;
        }
        
        html += `
            </div>
          </div>
        `;
      }
    } else if (balances.total_evr === 0) {
      html += `
        <div class="alert alert-warning">
          <i class="bi bi-exclamation-triangle-fill"></i> Your wallet is empty. Generate an address to receive funds.
        </div>
      `;
    }
    
    balancesContainer.innerHTML = html;
  }).catch(error => {
    console.error('Error loading balances:', error);
    balancesContainer.innerHTML = `<div class="alert alert-danger">Error loading balances: ${error.message || 'Unknown error'}</div>`;
  });
}

// Load UTXOs
function loadUTXOs() {
  const utxoList = document.getElementById('utxo-list');
  utxoList.innerHTML = '<tr><td colspan="6" class="text-center">Loading UTXOs...</td></tr>';
  
  eel.get_utxos()().then(utxos => {
    if (!utxos || utxos.length === 0) {
      utxoList.innerHTML = '<tr><td colspan="6" class="text-center">No UTXOs found</td></tr>';
      return;
    }
    
    // Sort by confirmation status and then txid
    utxos.sort((a, b) => {
      if (a.confirmations !== b.confirmations) {
        return b.confirmations - a.confirmations; // Higher confirmations first
      }
      return a.txid.localeCompare(b.txid);
    });
    
    // Render UTXOs
    utxoList.innerHTML = utxos.map(utxo => `
      <tr>
        <td class="font-monospace small text-truncate" style="max-width: 150px;">${utxo.txid}</td>
        <td>${utxo.vout}</td>
        <td class="font-monospace small text-truncate" style="max-width: 150px;">${utxo.address}</td>
        <td>${utxo.asset}</td>
        <td>${utxo.amount.toFixed(8)}</td>
        <td>
          <span class="badge bg-${utxo.confirmations > 0 ? 'success' : 'warning'}">
            ${utxo.status} ${utxo.confirmations > 0 ? `(${utxo.confirmations})` : ''}
          </span>
        </td>
      </tr>
    `).join('');
  }).catch(error => {
    console.error('Error loading UTXOs:', error);
    utxoList.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading UTXOs: ${error.message || 'Unknown error'}</td></tr>`;
  });
}

// Load wallet list for receive tab
function loadWalletList() {
  const walletSelect = document.getElementById('wallet-select');
  
  eel.get_wallet_list()().then(wallets => {
    // Save current selection if any
    const currentValue = walletSelect.value;
    
    // Clear options
    walletSelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = 'default';
    defaultOption.textContent = 'Default Wallet';
    walletSelect.appendChild(defaultOption);
    
    // Add wallet options
    if (wallets && wallets.length > 0) {
      wallets.forEach(wallet => {
        if (wallet !== 'default') {
          const option = document.createElement('option');
          option.value = wallet;
          option.textContent = wallet;
          walletSelect.appendChild(option);
        }
      });
    }
    
    // Restore selection if valid
    if (currentValue && Array.from(walletSelect.options).some(opt => opt.value === currentValue)) {
      walletSelect.value = currentValue;
    }
  }).catch(error => {
    console.error('Error loading wallet list:', error);
  });
}

// Send funds
function sendFunds() {
  const address = document.getElementById('send-address').value.trim();
  const amount = document.getElementById('send-amount').value.trim();
  const dryRun = document.getElementById('send-dry-run').checked;
  const statusElement = document.getElementById('send-status');
  
  // Validate inputs
  if (!address || !amount) {
    statusElement.textContent = 'Please enter a valid address and amount';
    statusElement.className = 'alert alert-danger';
    statusElement.classList.remove('d-none');
    return;
  }
  
  // Show sending status
  statusElement.textContent = 'Sending transaction...';
  statusElement.className = 'alert alert-warning';
  statusElement.classList.remove('d-none');
  
  // Disable form during submission
  const submitButton = document.querySelector('#send-form button[type="submit"]');
  submitButton.disabled = true;
  
  // Call backend to send funds
  eel.send_evr(address, parseFloat(amount), dryRun)().then(result => {
    // Re-enable form
    submitButton.disabled = false;
    
    if (result.success) {
      // Show success message
      statusElement.textContent = result.message;
      statusElement.className = 'alert alert-success';
      
      // Add txid if available
      if (result.txid) {
        const txidElement = document.createElement('div');
        txidElement.className = 'mt-2 small';
        txidElement.innerHTML = `Transaction ID: <code>${result.txid}</code>`;
        statusElement.appendChild(txidElement);
      }
      
      // Refresh wallet data after sending (if not dry run)
      if (!dryRun) {
        // Wait a moment for transaction to be processed
        setTimeout(refreshWallet, 2000);
      }
    } else {
      // Show error message
      statusElement.textContent = `Error: ${result.error}`;
      statusElement.className = 'alert alert-danger';
    }
  }).catch(error => {
    // Re-enable form
    submitButton.disabled = false;
    
    // Show error message
    statusElement.textContent = `Error: ${error.message || 'Unknown error'}`;
    statusElement.className = 'alert alert-danger';
    console.error('Send transaction error:', error);
  });
}

// Generate new address
function generateAddress() {
  const wallet = document.getElementById('wallet-select').value;
  const label = document.getElementById('address-label').value.trim();
  const statusElement = document.getElementById('receive-status');
  const resultElement = document.getElementById('address-result');
  
  // Show generating status
  statusElement.textContent = 'Generating address...';
  statusElement.className = 'alert alert-info';
  statusElement.classList.remove('d-none');
  
  // Hide previous result
  resultElement.classList.add('d-none');
  
  // Disable form during generation
  const submitButton = document.querySelector('#receive-form button[type="submit"]');
  submitButton.disabled = true;
  
  // Call backend to generate address
  eel.generate_receive_address(wallet, label || null)().then(result => {
    // Re-enable form
    submitButton.disabled = false;
    
    if (result.success) {
      // Hide status message
      statusElement.classList.add('d-none');
      
      // Show address
      document.getElementById('new-address').textContent = result.address;
      
      // Generate QR code
      generateQR(result.address);
      
      // Show result
      resultElement.classList.remove('d-none');
      
      // Refresh wallet data
      refreshWallet();
    } else {
      // Show error message
      statusElement.textContent = `Error: ${result.error}`;
      statusElement.className = 'alert alert-danger';
    }
  }).catch(error => {
    // Re-enable form
    submitButton.disabled = false;
    
    // Show error message
    statusElement.textContent = `Error: ${error.message || 'Unknown error'}`;
    statusElement.className = 'alert alert-danger';
    console.error('Generate address error:', error);
  });
}

// Generate QR code for address
function generateQR(address) {
  const qrContainer = document.getElementById('qr-code');
  qrContainer.innerHTML = '';
  
  // Use QRCode.js if available, otherwise show text
  if (typeof QRCode !== 'undefined') {
    new QRCode(qrContainer, {
      text: address,
      width: 150,
      height: 150
    });
  } else {
    qrContainer.innerText = 'QR Code generation not available';
  }
}

// Make refresh wallet function available globally
window.refreshWallet = refreshWallet;

// Add debugging button to the wallet view
function addDebugButton() {
    const walletContainer = document.getElementById('wallet-container');
    if (!walletContainer) return;
    
    const debugButton = document.createElement('button');
    debugButton.className = 'btn btn-secondary';
    debugButton.innerText = 'Debug Wallet Structure';
    debugButton.style.marginBottom = '15px';
    
    debugButton.addEventListener('click', async () => {
        try {
            // Get raw wallet data structure
            const walletInfo = await eel.get_wallet_info()();
            
            // Create and show modal
            const modal = document.createElement('div');
            modal.className = 'modal fade show';
            modal.style.display = 'block';
            modal.setAttribute('tabindex', '-1');
            
            // Format wallet info with JSON.stringify with indentation
            const walletInfoStr = JSON.stringify(walletInfo, null, 2);
            
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Wallet Data Structure</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <pre style="max-height: 400px; overflow-y: auto;">${walletInfoStr}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to body
            document.body.appendChild(modal);
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
            
            // Handle close button
            const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            closeButtons.forEach(button => {
                button.addEventListener('click', () => {
                    modal.remove();
                    backdrop.remove();
                });
            });
            
            // Console log for developers
            console.log('Wallet Info:', walletInfo);
        } catch (error) {
            console.error('Error getting wallet info:', error);
            alert('Error getting wallet info: ' + error);
        }
    });
    
    // Add button at the top of wallet container
    walletContainer.prepend(debugButton);
}

// Call this after initializing wallet view
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the wallet view to load
    setTimeout(() => {
        addDebugButton();
    }, 1000);
}); 