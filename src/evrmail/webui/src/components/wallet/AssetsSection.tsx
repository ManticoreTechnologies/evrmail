import React, { useState } from 'react';

interface AssetsSectionProps {
  assets: Record<string, Record<string, number>>;
}

const AssetsSection: React.FC<AssetsSectionProps> = ({ assets }) => {
  const [filter, setFilter] = useState('');

  // Get all asset names
  const assetNames = Object.keys(assets);

  // Filter assets based on search input
  const filteredAssetNames = assetNames.filter(assetName => 
    assetName.toLowerCase().includes(filter.toLowerCase())
  );

  // Check if we have any assets at all
  const hasAssets = assetNames.length > 0;

  // Format asset amount
  const formatAmount = (amount: number): string => {
    return amount.toFixed(8);
  };

  // Get total amount for an asset across all wallets
  const getTotalAssetAmount = (assetName: string): number => {
    let total = 0;
    const assetWallets = assets[assetName] || {};
    Object.values(assetWallets).forEach(amount => {
      total += amount;
    });
    return total;
  };

  if (!hasAssets) {
    return <div className="empty-state">No assets found in your wallet</div>;
  }

  return (
    <div className="assets-section">
      <h2>Blockchain Assets</h2>
      
      <div className="filter-container">
        <input
          type="text"
          placeholder="Search assets..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="asset-filter"
        />
      </div>
      
      {filteredAssetNames.length === 0 ? (
        <div className="empty-state">No assets match your search</div>
      ) : (
        <div className="assets-list">
          {filteredAssetNames.map(assetName => {
            const assetWallets = assets[assetName] || {};
            const totalAmount = getTotalAssetAmount(assetName);
            
            return (
              <div key={assetName} className="asset-item">
                <div className="asset-header">
                  <h3 className="asset-name">{assetName}</h3>
                  <div className="asset-total">{formatAmount(totalAmount)}</div>
                </div>
                
                <div className="asset-wallets">
                  {Object.entries(assetWallets).map(([address, amount]) => (
                    <div key={address} className="asset-wallet-item">
                      <div className="asset-address">{address}</div>
                      <div className="asset-amount">{formatAmount(amount)}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AssetsSection; 