import { loadTemplate } from '../../utils.js';

export async function initHomeView() {
  await loadTemplate('components/Home/home.html', 'home-view');
  loadNetworkStatus();
  loadQuickStats();
}

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