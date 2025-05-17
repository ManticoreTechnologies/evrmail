import React, { useState } from 'react';
import { generateReceiveAddress } from '../../utils/bridge';

interface ReceiveSectionProps {
  backend: Backend | null;
  walletList: string[];
  onAddressGenerated: () => void;
}

const ReceiveSection: React.FC<ReceiveSectionProps> = ({ 
  backend, 
  walletList, 
  onAddressGenerated 
}) => {
  const [selectedWallet, setSelectedWallet] = useState('default');
  const [addressLabel, setAddressLabel] = useState('');
  const [generatedAddress, setGeneratedAddress] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Handle generating a new address
  const handleGenerateAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setError(null);
    setGeneratedAddress(null);
    setCopied(false);
    setGenerating(true);
    
    try {
      if (!backend) {
        throw new Error('Backend not available');
      }
      
      const result = await generateReceiveAddress(
        backend,
        selectedWallet,
        addressLabel.trim() || undefined
      );
      
      if (result.success && result.address) {
        setGeneratedAddress(result.address);
        onAddressGenerated();
      } else {
        setError(result.error || 'Failed to generate address');
      }
    } catch (err) {
      console.error('Error generating address:', err);
      setError('An error occurred while generating the address');
    } finally {
      setGenerating(false);
    }
  };

  // Handle copying address to clipboard
  const handleCopyAddress = () => {
    if (generatedAddress) {
      navigator.clipboard.writeText(generatedAddress)
        .then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        })
        .catch(err => {
          console.error('Failed to copy:', err);
        });
    }
  };

  return (
    <div className="receive-section">
      <h2>Receive EVR</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleGenerateAddress}>
        <div className="form-group">
          <label htmlFor="walletSelect">Wallet</label>
          <select
            id="walletSelect"
            value={selectedWallet}
            onChange={(e) => setSelectedWallet(e.target.value)}
            disabled={generating}
          >
            <option value="default">Default Wallet</option>
            {walletList
              .filter(wallet => wallet !== 'default')
              .map(wallet => (
                <option key={wallet} value={wallet}>
                  {wallet}
                </option>
              ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="addressLabel">Address Label (optional)</label>
          <input
            type="text"
            id="addressLabel"
            value={addressLabel}
            onChange={(e) => setAddressLabel(e.target.value)}
            placeholder="Enter a label for this address"
            disabled={generating}
          />
        </div>
        
        <button
          type="submit"
          className="generate-button"
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate New Address'}
        </button>
      </form>
      
      {generatedAddress && (
        <div className="generated-address-container">
          <h3>New Address Generated</h3>
          
          <div className="address-display">
            <code>{generatedAddress}</code>
            <button 
              className="copy-button" 
              onClick={handleCopyAddress}
              title="Copy to clipboard"
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
          
          <div className="qr-placeholder">
            {/* QR code would be generated here */}
            <div className="qr-note">
              QR code for {generatedAddress.slice(0, 8)}...
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReceiveSection; 