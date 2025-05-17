import React, { useState } from 'react';
import { createNewWallet } from '../../utils/bridge';
import './Wallet.css';

interface WalletManageSectionProps {
  backend: Backend | null;
  walletList: string[];
  onWalletCreated: () => void;
}

const WalletManageSection: React.FC<WalletManageSectionProps> = ({ 
  backend, 
  walletList, 
  onWalletCreated 
}) => {
  // State for new wallet creation
  const [walletName, setWalletName] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [showPassphrase, setShowPassphrase] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{
    name: string;
    mnemonic: string;
    message: string;
  } | null>(null);

  // Create a new wallet
  const handleCreateWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await createNewWallet(backend, walletName, passphrase);

      if (result.success && result.name && result.mnemonic) {
        setSuccess({
          name: result.name,
          mnemonic: result.mnemonic,
          message: result.message || `Wallet "${result.name}" created successfully!`
        });
        setWalletName('');
        setPassphrase('');
        onWalletCreated(); // Refresh wallet list
      } else {
        setError(result.error || 'Unknown error creating wallet');
      }
    } catch (err) {
      console.error('Error creating wallet:', err);
      setError('Failed to create wallet. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="wallet-manage-section">
      <h2>Wallet Management</h2>
      
      <div className="wallet-list-container">
        <h3>Your Wallets</h3>
        <div className="wallet-list">
          {walletList.length === 0 ? (
            <div className="no-wallets-message">No wallets found</div>
          ) : (
            <ul>
              {walletList.map(wallet => (
                <li key={wallet} className="wallet-item">
                  <span className="wallet-name">{wallet}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      
      <div className="create-wallet-container">
        <h3>Create New Wallet</h3>
        
        {error && <div className="error-message">{error}</div>}
        
        {success ? (
          <div className="success-box">
            <p className="success-message">{success.message}</p>
            
            <div className="wallet-details">
              <p><strong>Wallet Name:</strong> {success.name}</p>
              
              <div className="mnemonic-box">
                <p><strong>Recovery Phrase (Mnemonic):</strong></p>
                <p className="mnemonic-phrase">{success.mnemonic}</p>
                <div className="mnemonic-warning">
                  <strong>IMPORTANT:</strong> Write down this recovery phrase and keep it in a safe place. 
                  This is the only way to recover your wallet if you lose access.
                  Anyone with access to this phrase can access your funds!
                </div>
              </div>
            </div>
            
            <button 
              className="new-wallet-button"
              onClick={() => setSuccess(null)}
            >
              Create Another Wallet
            </button>
          </div>
        ) : (
          <form onSubmit={handleCreateWallet}>
            <div className="form-group">
              <label htmlFor="walletName">Wallet Name (optional)</label>
              <input
                type="text"
                id="walletName"
                value={walletName}
                onChange={(e) => setWalletName(e.target.value)}
                placeholder="Enter wallet name or leave blank for random name"
                disabled={creating}
              />
              <small className="form-help">
                If left blank, a random name will be generated
              </small>
            </div>
            
            <div className="form-group">
              <label htmlFor="passphrase">Optional Passphrase</label>
              <div className="password-field">
                <input
                  type={showPassphrase ? "text" : "password"}
                  id="passphrase"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  placeholder="Enter a passphrase for added security (optional)"
                  disabled={creating}
                />
                <button 
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassphrase(!showPassphrase)}
                >
                  {showPassphrase ? "Hide" : "Show"}
                </button>
              </div>
              <small className="form-help">
                Adding a passphrase increases security but must be remembered
              </small>
            </div>
            
            <button
              type="submit"
              className="create-button"
              disabled={creating}
            >
              {creating ? "Creating..." : "Create New Wallet"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default WalletManageSection; 