import React, { useState, useEffect } from 'react';
import { getWalletBalances, getWalletAddresses, getWalletList } from '../../utils/bridge';
import BalanceSection from './BalanceSection';
import SendSection from './SendSection';
import ReceiveSection from './ReceiveSection';
import AddressesSection from './AddressesSection';
import AssetsSection from './AssetsSection';
import WalletManageSection from './WalletManageSection';
import './Wallet.css';

interface WalletViewProps {
  backend: Backend | null;
}

// Define wallet tab types
type WalletTab = 'overview' | 'send' | 'receive' | 'addresses' | 'assets' | 'manage';

const WalletView: React.FC<WalletViewProps> = ({ backend }) => {
  // State for wallet data
  const [balances, setBalances] = useState<any>(null);
  const [addresses, setAddresses] = useState<any[]>([]);
  const [walletList, setWalletList] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<WalletTab>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Load wallet data
  useEffect(() => {
    const loadWalletData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Load balances
        const balancesData = await getWalletBalances(backend);
        setBalances(balancesData);

        // Load addresses
        const addressesData = await getWalletAddresses(backend);
        setAddresses(addressesData || []);

        // Load wallet list
        const walletListData = await getWalletList(backend);
        setWalletList(walletListData || []);
      } catch (err) {
        console.error('Error loading wallet data:', err);
        setError('Failed to load wallet data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (backend) {
      loadWalletData();
    }
  }, [backend, refreshTrigger]);

  // Check if we have any assets
  const hasAssets = balances && 
    balances.assets && 
    Object.keys(balances.assets).length > 0 && 
    Object.values(balances.assets).some(
      (wallet: any) => Object.keys(wallet).length > 0
    );

  // Trigger a refresh of wallet data
  const refreshWallet = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Render the active tab content
  const renderTabContent = () => {
    if (loading) {
      return <div className="loading">Loading wallet data...</div>;
    }

    if (error) {
      return <div className="error-message">{error}</div>;
    }

    switch (activeTab) {
      case 'overview':
        return (
          <BalanceSection 
            balances={balances} 
            addresses={addresses}
          />
        );
      case 'send':
        return (
          <SendSection 
            backend={backend} 
            balances={balances}
            onTransactionSent={refreshWallet}
          />
        );
      case 'receive':
        return (
          <ReceiveSection 
            backend={backend} 
            walletList={walletList}
            onAddressGenerated={refreshWallet}
          />
        );
      case 'addresses':
        return (
          <AddressesSection 
            addresses={addresses}
            balances={balances?.evr || {}}
          />
        );
      case 'assets':
        return (
          <AssetsSection 
            assets={balances?.assets || {}}
          />
        );
      case 'manage':
        return (
          <WalletManageSection 
            backend={backend}
            walletList={walletList}
            onWalletCreated={refreshWallet}
          />
        );
      default:
        return <div>Unknown tab</div>;
    }
  };

  return (
    <div className="wallet-view">
      <h1>Wallet</h1>
      
      <div className="wallet-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'send' ? 'active' : ''}`}
          onClick={() => setActiveTab('send')}
        >
          Send
        </button>
        <button 
          className={`tab-button ${activeTab === 'receive' ? 'active' : ''}`}
          onClick={() => setActiveTab('receive')}
        >
          Receive
        </button>
        <button 
          className={`tab-button ${activeTab === 'addresses' ? 'active' : ''}`}
          onClick={() => setActiveTab('addresses')}
        >
          Addresses
        </button>
        {hasAssets && (
          <button 
            className={`tab-button ${activeTab === 'assets' ? 'active' : ''}`}
            onClick={() => setActiveTab('assets')}
          >
            Assets
          </button>
        )}
        <button 
          className={`tab-button ${activeTab === 'manage' ? 'active' : ''}`}
          onClick={() => setActiveTab('manage')}
        >
          Manage
        </button>
        <button 
          className="refresh-button"
          onClick={refreshWallet}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>
      
      <div className="tab-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default WalletView; 