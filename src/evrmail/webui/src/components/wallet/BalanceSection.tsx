import React from 'react';

interface BalanceSectionProps {
  balances: {
    total_evr: number;
    evr: Record<string, number>;
    assets: Record<string, Record<string, number>>;
  } | null;
  addresses: Array<{
    address: string;
    label: string;
    wallet: string;
  }>;
}

const BalanceSection: React.FC<BalanceSectionProps> = ({ balances, addresses }) => {
  if (!balances) {
    return <div className="empty-state">No balance information available</div>;
  }

  // Find label for an address
  const getAddressLabel = (address: string): string => {
    const addressInfo = addresses.find(addr => addr.address === address);
    return addressInfo?.label || 'Unnamed';
  };

  // Format EVR amount
  const formatAmount = (amount: number): string => {
    return amount.toFixed(8);
  };

  return (
    <div className="balance-section">
      <div className="total-balance-card">
        <h2>Total Balance</h2>
        <div className="total-balance-amount">{formatAmount(balances.total_evr)} EVR</div>
      </div>

      <div className="balance-details">
        <div className="evr-balances-card">
          <h2>EVR Balances</h2>
          
          {Object.keys(balances.evr).length === 0 ? (
            <div className="empty-state">No EVR balances found</div>
          ) : (
            <div className="balance-list">
              {Object.entries(balances.evr).map(([address, amount]) => (
                <div key={address} className="balance-item">
                  <div className="balance-info">
                    <div className="address-label">{getAddressLabel(address)}</div>
                    <div className="address" title={address}>
                      {address}
                    </div>
                  </div>
                  <div className="balance-amount">{formatAmount(amount)} EVR</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {Object.keys(balances.assets).length > 0 && (
          <div className="assets-preview-card">
            <h2>Assets</h2>
            <div className="assets-summary">
              {Object.entries(balances.assets).map(([assetName, walletAssets]) => (
                <div key={assetName} className="asset-summary-item">
                  <div className="asset-name">{assetName}</div>
                  <div className="asset-wallets">
                    {Object.keys(walletAssets).length} wallet{Object.keys(walletAssets).length !== 1 ? 's' : ''}
                  </div>
                </div>
              ))}
            </div>
            <div className="asset-note">
              Switch to the Assets tab for details
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BalanceSection; 