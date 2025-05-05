// Wallet view implementation
function initWalletView() {
  const view = document.getElementById('wallet-view');
  
  // Create wallet tabs
  view.innerHTML = `
    <div class="container">
      <h1 class="text-center mb-4">💼 Wallet Overview</h1>
      
      <ul class="nav nav-tabs" id="walletTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="addresses-tab" data-bs-toggle="tab" data-bs-target="#addresses" type="button" role="tab" aria-controls="addresses" aria-selected="true">Addresses</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="balances-tab" data-bs-toggle="tab" data-bs-target="#balances" type="button" role="tab" aria-controls="balances" aria-selected="false">Balances</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="utxos-tab" data-bs-toggle="tab" data-bs-target="#utxos" type="button" role="tab" aria-controls="utxos" aria-selected="false">UTXOs</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="send-tab" data-bs-toggle="tab" data-bs-target="#send" type="button" role="tab" aria-controls="send" aria-selected="false">Send</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="receive-tab" data-bs-toggle="tab" data-bs-target="#receive" type="button" role="tab" aria-controls="receive" aria-selected="false">Receive</button>
        </li>
      </ul>
      
      <div class="tab-content p-3 border border-top-0 rounded-bottom" id="walletTabsContent" style="background-color: var(--darker-bg);">
        <!-- Addresses Tab -->
        <div class="tab-pane fade show active" id="addresses" role="tabpanel" aria-labelledby="addresses-tab">
          <div class="d-flex justify-content-between mb-3">
            <h4 class="text-primary">Derived Addresses</h4>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="only-labeled" value="false">
              <label class="form-check-label" for="only-labeled">Only show user-labeled addresses</label>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table table-dark table-hover">
              <thead>
                <tr>
                  <th>Index</th>
                  <th>Label</th>
                  <th>Address</th>
                  <th>Path</th>
                </tr>
              </thead>
              <tbody id="addresses-table-body">
                <tr>
                  <td colspan="4" class="text-center">Loading addresses...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Balances Tab -->
        <div class="tab-pane fade" id="balances" role="tabpanel" aria-labelledby="balances-tab">
          <h4 class="text-primary mb-3">Wallet Balances</h4>
          <div id="total-balance"></div>
          
          <h5 class="mt-4">EVR Balances</h5>
          <div class="table-responsive">
            <table class="table table-dark table-hover">
              <thead>
                <tr>
                  <th>Address</th>
                  <th>EVR Balance</th>
                </tr>
              </thead>
              <tbody id="evr-balances-table">
                <tr>
                  <td colspan="2" class="text-center">Loading balances...</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <h5 class="mt-4">Asset Balances</h5>
          <div class="table-responsive">
            <table class="table table-dark table-hover">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Address</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody id="asset-balances-table">
                <tr>
                  <td colspan="3" class="text-center">Loading asset balances...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- UTXOs Tab -->
        <div class="tab-pane fade" id="utxos" role="tabpanel" aria-labelledby="utxos-tab">
          <div class="d-flex justify-content-between mb-3">
            <h4 class="text-primary">UTXO Overview</h4>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="show-spent" value="false">
              <label class="form-check-label" for="show-spent">Show Spent</label>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table table-dark table-hover">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Address</th>
                  <th>Asset</th>
                  <th>Amount</th>
                  <th>TXID</th>
                  <th>Confirmations</th>
                </tr>
              </thead>
              <tbody id="utxos-table-body">
                <tr>
                  <td colspan="6" class="text-center">Loading UTXOs...</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="text-center mt-3">
            <button id="refresh-utxos" class="btn btn-primary">
              <i class="bi bi-arrow-clockwise"></i> Refresh UTXOs
            </button>
          </div>
        </div>
        
        <!-- Send Tab -->
        <div class="tab-pane fade" id="send" role="tabpanel" aria-labelledby="send-tab">
          <h4 class="text-primary mb-3">Send EVR or Assets</h4>
          <form id="send-form">
            <div class="mb-3">
              <label for="send-asset" class="form-label">Select Asset</label>
              <select class="form-select" id="send-asset" required>
                <option value="EVR">EVR</option>
                <!-- Other assets will be loaded dynamically -->
              </select>
            </div>
            
            <div class="mb-3">
              <label for="send-address" class="form-label">Destination Address</label>
              <input type="text" class="form-control" id="send-address" placeholder="Enter recipient address" required>
            </div>
            
            <div class="mb-3">
              <label for="send-amount" class="form-label">Amount</label>
              <input type="number" class="form-control" id="send-amount" placeholder="Enter amount to send" required step="0.00000001">
            </div>
            
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="send-dry-run">
              <label class="form-check-label" for="send-dry-run">🧪 Dry-Run Only (simulate, no broadcast)</label>
            </div>
            
            <div id="send-status" class="alert d-none" role="alert"></div>
            
            <div class="text-center">
              <button type="submit" class="btn btn-primary">
                <i class="bi bi-send"></i> Send Transaction
              </button>
            </div>
          </form>
        </div>
        
        <!-- Receive Tab -->
        <div class="tab-pane fade" id="receive" role="tabpanel" aria-labelledby="receive-tab">
          <h4 class="text-primary mb-3">Receive EVR / Assets</h4>
          
          <div class="row">
            <div class="col-md-6">
              <div class="mb-3">
                <label for="receive-wallet" class="form-label">Select Wallet</label>
                <select class="form-select" id="receive-wallet">
                  <option value="default">Default Wallet</option>
                </select>
              </div>
              
              <div class="mb-3">
                <label for="receive-label" class="form-label">Optional Label</label>
                <input type="text" class="form-control" id="receive-label" placeholder="Enter a friendly name for this address">
              </div>
              
              <div class="text-center mb-3">
                <button id="generate-address" class="btn btn-primary">
                  <i class="bi bi-qr-code"></i> Generate New Address
                </button>
              </div>
            </div>
            
            <div class="col-md-6 text-center">
              <div id="qr-container" class="mb-3 p-3 border rounded" style="background-color: white; display: none;">
                <img id="qr-code" src="" alt="QR Code" style="max-width: 100%;">
              </div>
            </div>
          </div>
          
          <div class="mb-3">
            <label for="receive-address" class="form-label">Receiving Address</label>
            <div class="input-group">
              <input type="text" class="form-control" id="receive-address" readonly>
              <button class="btn btn-outline-secondary" type="button" id="copy-address">
                <i class="bi bi-clipboard"></i> Copy
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Load data
  loadAddresses();
  loadBalances();
  loadUtxos();
  setupSendTab();
  setupReceiveTab();
  
  // Set up event listeners
  document.getElementById('only-labeled').addEventListener('change', loadAddresses);
  document.getElementById('show-spent').addEventListener('change', loadUtxos);
  document.getElementById('refresh-utxos').addEventListener('click', loadUtxos);
}

// Load wallet addresses
function loadAddresses() {
  const onlyLabeled = document.getElementById('only-labeled').checked;
  
  eel.get_wallet_addresses()().then(addresses => {
    const tableBody = document.getElementById('addresses-table-body');
    tableBody.innerHTML = '';
    
    // Filter if needed
    const filteredAddresses = onlyLabeled ? 
      addresses.filter(a => a.friendly_name && !a.friendly_name.startsWith('address_')) : 
      addresses;
    
    if (filteredAddresses.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="4" class="text-center">No addresses found</td></tr>`;
      return;
    }
    
    filteredAddresses.forEach(addr => {
      const row = document.createElement('tr');
      
      row.innerHTML = `
        <td>${addr.index}</td>
        <td class="text-primary">${addr.friendly_name || ''}</td>
        <td>
          <div class="d-flex justify-content-between align-items-center">
            <code>${addr.address}</code>
            <button class="btn btn-sm btn-outline-primary copy-btn" data-copy="${addr.address}">
              <i class="bi bi-clipboard"></i>
            </button>
          </div>
        </td>
        <td><small>${addr.path}</small></td>
      `;
      
      tableBody.appendChild(row);
    });
    
    // Set up copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-copy');
        navigator.clipboard.writeText(text).then(() => {
          // Show tooltip or toast
          alert(`Copied: ${text}`);
        });
      });
    });
  });
}

// Load wallet balances
function loadBalances() {
  eel.get_wallet_balances()().then(balances => {
    // Update total balance
    const totalBalanceElement = document.getElementById('total-balance');
    totalBalanceElement.innerHTML = `
      <div class="alert alert-success">
        <strong>Total EVR: ${balances.total_evr.toFixed(8)}</strong>
      </div>
    `;
    
    // Update EVR balances table
    const evrTable = document.getElementById('evr-balances-table');
    evrTable.innerHTML = '';
    
    Object.entries(balances.evr).forEach(([address, amount]) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${address}</td>
        <td class="text-end">${amount.toFixed(8)}</td>
      `;
      evrTable.appendChild(row);
    });
    
    // Update asset balances table
    const assetTable = document.getElementById('asset-balances-table');
    assetTable.innerHTML = '';
    
    Object.entries(balances.assets).forEach(([asset, addressMap]) => {
      Object.entries(addressMap).forEach(([address, amount]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${asset}</td>
          <td>${address}</td>
          <td class="text-end">${amount.toFixed(8)}</td>
        `;
        assetTable.appendChild(row);
      });
    });
    
    // Also populate the send asset dropdown
    const sendAssetSelect = document.getElementById('send-asset');
    sendAssetSelect.innerHTML = '<option value="EVR">EVR</option>';
    
    Object.keys(balances.assets).forEach(asset => {
      const option = document.createElement('option');
      option.value = asset;
      option.textContent = asset;
      sendAssetSelect.appendChild(option);
    });
  });
}

// Load UTXOs
function loadUtxos() {
  const showSpent = document.getElementById('show-spent').checked;
  
  eel.get_utxos()().then(utxos => {
    const tableBody = document.getElementById('utxos-table-body');
    tableBody.innerHTML = '';
    
    // Filter if needed
    const filteredUtxos = showSpent ? utxos : utxos.filter(u => !u.spent);
    
    if (filteredUtxos.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center">No UTXOs found</td></tr>`;
      return;
    }
    
    filteredUtxos.forEach(utxo => {
      const row = document.createElement('tr');
      const statusColor = utxo.spent ? 'danger' : (utxo.status.includes('Unconfirmed') ? 'warning' : 'success');
      
      row.innerHTML = `
        <td><span class="badge bg-${statusColor}">${utxo.status}</span></td>
        <td><small>${utxo.address}</small></td>
        <td>${utxo.asset}</td>
        <td class="text-end">${utxo.amount.toFixed(8)}</td>
        <td>
          <div class="d-flex justify-content-between align-items-center">
            <code class="small">${utxo.txid.substring(0, 10)}...</code>
            <button class="btn btn-sm btn-outline-primary copy-btn" data-copy="${utxo.txid}">
              <i class="bi bi-clipboard"></i>
            </button>
          </div>
        </td>
        <td class="text-center">${utxo.confirmations}</td>
      `;
      
      tableBody.appendChild(row);
    });
    
    // Set up copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-copy');
        navigator.clipboard.writeText(text).then(() => {
          // Show tooltip or toast
          alert(`Copied: ${text}`);
        });
      });
    });
  });
}

// Set up send tab
function setupSendTab() {
  const sendForm = document.getElementById('send-form');
  sendForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const asset = document.getElementById('send-asset').value;
    const address = document.getElementById('send-address').value;
    const amount = parseFloat(document.getElementById('send-amount').value);
    const dryRun = document.getElementById('send-dry-run').checked;
    
    // Show sending status
    const statusElement = document.getElementById('send-status');
    statusElement.className = 'alert alert-warning';
    statusElement.textContent = '⏳ Processing transaction...';
    statusElement.classList.remove('d-none');
    
    // Send transaction (reusing the message sending function for simplicity)
    eel.send_message(address, `Send ${amount} ${asset}`, `Transaction of ${amount} ${asset}`, asset, dryRun)().then(result => {
      if (result.success) {
        // Show success message
        statusElement.className = 'alert alert-success';
        statusElement.textContent = `✅ ${result.message}`;
        
        // Clear form after successful transaction
        if (!dryRun) {
          setTimeout(() => {
            document.getElementById('send-address').value = '';
            document.getElementById('send-amount').value = '';
          }, 3000);
        }
      } else {
        // Show error message
        statusElement.className = 'alert alert-danger';
        statusElement.textContent = `❌ Error: ${result.error}`;
      }
    });
  });
}

// Set up receive tab
function setupReceiveTab() {
  const generateButton = document.getElementById('generate-address');
  const copyButton = document.getElementById('copy-address');
  
  // Generate address button
  generateButton.addEventListener('click', () => {
    const label = document.getElementById('receive-label').value;
    const wallet = document.getElementById('receive-wallet').value;
    
    // In a real implementation, we would generate a new address
    // For this simulation, use a fixed address
    const address = "EaB9Ru8187mzJUgYKgYKMRsz7WYGi3JrVx";
    
    // Display the address
    document.getElementById('receive-address').value = address;
    
    // Show QR code (simulated)
    document.getElementById('qr-code').src = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + encodeURIComponent(address);
    document.getElementById('qr-container').style.display = 'block';
  });
  
  // Copy address button
  copyButton.addEventListener('click', () => {
    const address = document.getElementById('receive-address').value;
    if (address) {
      navigator.clipboard.writeText(address).then(() => {
        alert(`Copied: ${address}`);
      });
    }
  });
} 