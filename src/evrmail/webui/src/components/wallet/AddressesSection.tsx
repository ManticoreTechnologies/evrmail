import React, { useState } from 'react';

interface AddressesSectionProps {
  addresses: Array<{
    index: number;
    address: string;
    path: string;
    label: string;
    wallet: string;
    public_key: string;
  }>;
  balances: Record<string, number>;
}

const AddressesSection: React.FC<AddressesSectionProps> = ({ addresses, balances }) => {
  const [filter, setFilter] = useState('');
  const [copied, setCopied] = useState<string | null>(null);

  // Filter addresses based on search input
  const filteredAddresses = addresses.filter(addr => {
    const searchTerm = filter.toLowerCase();
    return (
      addr.address.toLowerCase().includes(searchTerm) ||
      addr.label.toLowerCase().includes(searchTerm) ||
      addr.wallet.toLowerCase().includes(searchTerm)
    );
  });

  // Sort by wallet and then by index
  const sortedAddresses = [...filteredAddresses].sort((a, b) => {
    // Sort by wallet name first
    if (a.wallet !== b.wallet) {
      return a.wallet.localeCompare(b.wallet);
    }
    // Then by index
    return a.index - b.index;
  });

  // Group addresses by wallet
  const addressesByWallet: Record<string, typeof addresses> = {};
  sortedAddresses.forEach(addr => {
    if (!addressesByWallet[addr.wallet]) {
      addressesByWallet[addr.wallet] = [];
    }
    addressesByWallet[addr.wallet].push(addr);
  });

  // Handle copying address to clipboard
  const handleCopyAddress = (address: string) => {
    navigator.clipboard.writeText(address)
      .then(() => {
        setCopied(address);
        setTimeout(() => setCopied(null), 2000);
      })
      .catch(err => {
        console.error('Failed to copy:', err);
      });
  };

  // Format EVR amount
  const formatAmount = (amount: number): string => {
    return amount.toFixed(8);
  };

  // Get balance for an address
  const getAddressBalance = (address: string): number => {
    return balances[address] || 0;
  };

  if (addresses.length === 0) {
    return <div className="empty-state">No addresses found</div>;
  }

  return (
    <div className="addresses-section">
      <h2>Wallet Addresses</h2>
      
      <div className="filter-container">
        <input
          type="text"
          placeholder="Search addresses, labels, or wallets..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="address-filter"
        />
      </div>
      
      {Object.keys(addressesByWallet).length === 0 ? (
        <div className="empty-state">No addresses match your search</div>
      ) : (
        Object.entries(addressesByWallet).map(([wallet, walletAddresses]) => (
          <div key={wallet} className="wallet-addresses-group">
            <h3 className="wallet-name">
              {wallet === 'default' ? 'Default Wallet' : wallet}
              <span className="address-count">
                {walletAddresses.length} address{walletAddresses.length !== 1 ? 'es' : ''}
              </span>
            </h3>
            
            <div className="addresses-list">
              {walletAddresses.map(addr => {
                const balance = getAddressBalance(addr.address);
                return (
                  <div key={addr.address} className="address-item">
                    <div className="address-index">{addr.index}</div>
                    
                    <div className="address-content">
                      <div className="address-label">
                        {addr.label || 'Unnamed'}
                      </div>
                      
                      <div className="address-row">
                        <div className="address">{addr.address}</div>
                        <button 
                          className="copy-button" 
                          onClick={() => handleCopyAddress(addr.address)}
                          title="Copy to clipboard"
                        >
                          {copied === addr.address ? '✓' : 'Copy'}
                        </button>
                      </div>
                      
                      <div className="address-details">
                        <div className="address-path" title="Derivation path">
                          {addr.path}
                        </div>
                        
                        <div className="address-balance">
                          {formatAmount(balance)} EVR
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default AddressesSection; 