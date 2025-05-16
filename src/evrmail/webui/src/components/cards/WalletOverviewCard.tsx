import React from 'react';

interface WalletOverviewCardProps {
  walletData: {
    balances: {
      total_evr: number;
      evr: Record<string, number>;
      assets: Record<string, Record<string, number>>;
    };
    addressCount: number;
    addresses: Array<{
      address: string;
      label: string;
    }>;
  } | null;
  backend: Backend | null;
}

const WalletOverviewCard: React.FC<WalletOverviewCardProps> = ({ walletData, backend }) => {
  // Format EVR amount to 8 decimal places
  const formatEVR = (amount: number) => {
    return amount.toFixed(8);
  };
  
  // Get all assets from the wallet data
  const getAssets = () => {
    if (!walletData?.balances?.assets) return [];
    
    const assets: Array<{ name: string, balance: number }> = [];
    
    Object.entries(walletData.balances.assets).forEach(([assetName, addresses]) => {
      // Sum up balance across all addresses
      const totalBalance = Object.values(addresses).reduce((sum, amount) => sum + amount, 0);
      assets.push({ name: assetName, balance: totalBalance });
    });
    
    return assets;
  };
  
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Wallet Overview</h3>
      </div>
      <div className="dashboard-card-content">
        <div className="wallet-overview-content">
          <div className="balance-section">
            <div className="balance-header">Total Balance</div>
            <div className="total-balance">
              {walletData?.balances ? formatEVR(walletData.balances.total_evr) : '0.00000000'} EVR
            </div>
          </div>
          
          <div className="assets-section">
            <div className="assets-header">Assets</div>
            <div className="asset-list">
              {getAssets().length === 0 ? (
                <div className="empty-state">No assets found</div>
              ) : (
                getAssets().map(asset => (
                  <div key={asset.name} className="asset-item">
                    <div className="asset-name">{asset.name}</div>
                    <div className="asset-balance">{formatEVR(asset.balance)}</div>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <div className="addresses-section">
            <div className="addresses-header">Addresses</div>
            <div className="addresses-info">
              <div className="addresses-count">{walletData?.addressCount || 0} addresses available</div>
              {walletData?.addresses && walletData.addresses.length > 0 && (
                <div className="primary-address">
                  <span className="address-label">Primary: </span>
                  <span className="address-value">
                    {walletData.addresses[0].address}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="dashboard-card-footer">
        <button className="view-wallet-button">Manage Wallet</button>
      </div>
    </div>
  );
};

export default WalletOverviewCard; 