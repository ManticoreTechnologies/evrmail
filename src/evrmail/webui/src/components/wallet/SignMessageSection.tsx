import React, { useState } from 'react';
import { signMessage, verifyMessage as verifyMessageFn } from '../../utils/bridge';

interface SignMessageSectionProps {
  backend: any | null;
  addresses: Array<{
    index: number;
    address: string;
    path: string;
    label: string;
    wallet: string;
    public_key: string;
  }>;
}

const SignMessageSection: React.FC<SignMessageSectionProps> = ({ backend, addresses }) => {
  // Signing state
  const [message, setMessage] = useState('');
  const [selectedAddress, setSelectedAddress] = useState('');
  const [signature, setSignature] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [signing, setSigning] = useState(false);
  const [success, setSuccess] = useState(false);
  
  // Verification state
  const [verifyAddress, setVerifyAddress] = useState('');
  const [verifyMessage, setVerifyMessage] = useState('');
  const [verifySignature, setVerifySignature] = useState('');
  const [verifyResult, setVerifyResult] = useState<null | boolean>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [showVerify, setShowVerify] = useState(false);

  // Handle signing message
  const handleSignMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset states
    setError(null);
    setSignature(null);
    setSuccess(false);
    
    // Validate inputs
    if (!message.trim()) {
      setError('Please enter a message to sign');
      return;
    }
    
    if (!selectedAddress) {
      setError('Please select an address');
      return;
    }
    
    // Sign message
    setSigning(true);
    
    try {
      if (!backend) {
        throw new Error('Backend not available');
      }
      
      const result = await signMessage(
        backend,
        selectedAddress,
        message.trim()
      );
      
      if (result.success) {
        setSignature(result.signature || null);
        setSuccess(true);
        
        // Pre-fill verification fields for convenience
        setVerifyAddress(selectedAddress);
        setVerifyMessage(message);
        setVerifySignature(result.signature || '');
      } else {
        setError(result.error || 'Failed to sign message');
      }
    } catch (err) {
      console.error('Error signing message:', err);
      setError('An error occurred while signing the message');
    } finally {
      setSigning(false);
    }
  };
  
  // Handle verifying message
  const handleVerifyMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset verification states
    setVerifyResult(null);
    setVerifyError(null);
    
    // Validate inputs
    if (!verifyMessage.trim() || !verifyAddress.trim() || !verifySignature.trim()) {
      setVerifyError('Please fill in all verification fields');
      return;
    }
    
    // Verify message
    setVerifying(true);
    
    try {
      if (!backend) {
        throw new Error('Backend not available');
      }
      
      const result = await verifyMessageFn(
        backend,
        verifyAddress,
        verifySignature,
        verifyMessage.trim()
      );
      
      setVerifyResult(result.valid);
      if (!result.valid && result.error) {
        setVerifyError(result.error);
      }
      setVerifying(false);
    } catch (err) {
      console.error('Error verifying message:', err);
      setVerifyError('An error occurred while verifying the message');
      setVerifyResult(false);
      setVerifying(false);
    }
  };

  // Copy signature to clipboard
  const copyToClipboard = () => {
    if (signature) {
      navigator.clipboard.writeText(signature)
        .then(() => {
          alert('Signature copied to clipboard');
        })
        .catch(err => {
          console.error('Could not copy text: ', err);
        });
    }
  };

  return (
    <div className="sign-message-section">
      <h2>Sign Message</h2>
      <p className="section-description">
        Sign a message with your wallet to prove ownership of an address.
        This is commonly used for authentication purposes.
      </p>
      
      {error && <div className="error-message">{error}</div>}
      
      {success && signature && (
        <div className="success-message">
          <p>Message signed successfully!</p>
          <div className="signature-display">
            <label>Signature:</label>
            <div className="signature-box">
              <code>{signature}</code>
              <button 
                type="button" 
                className="copy-button"
                onClick={copyToClipboard}
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSignMessage} className="sign-message-form">
        <div className="form-group">
          <label htmlFor="signing-address">Signing Address</label>
          <select
            id="signing-address"
            value={selectedAddress}
            onChange={(e) => setSelectedAddress(e.target.value)}
            disabled={signing}
            required
            className="full-width-input"
          >
            <option value="">Select an address</option>
            {addresses.map((addr) => (
              <option key={addr.address} value={addr.address}>
                {addr.label ? `${addr.label} (${addr.address})` : addr.address}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="message">Message</label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter message to sign"
            rows={4}
            disabled={signing}
            required
            className="full-width-input"
          />
        </div>
        
        <button
          type="submit"
          className="sign-button"
          disabled={signing || !selectedAddress || !message}
        >
          {signing ? 'Signing...' : 'Sign Message'}
        </button>
      </form>
      
      <div className="verify-section-toggle">
        <button 
          onClick={() => setShowVerify(!showVerify)} 
          className="toggle-verify-button"
        >
          {showVerify ? 'Hide Verification' : 'Show Verification'}
        </button>
      </div>
      
      {showVerify && (
        <div className="verify-message-section">
          <h3>Verify Message</h3>
          <p className="section-description">
            Verify that a message was signed by the owner of a specific address.
          </p>
          
          {verifyError && <div className="error-message">{verifyError}</div>}
          
          {verifyResult !== null && (
            <div className={verifyResult ? "success-message" : "error-message"}>
              {verifyResult 
                ? "Signature is valid! The message was signed by this address." 
                : "Invalid signature. The message was not signed by this address or has been altered."}
            </div>
          )}
          
          <form onSubmit={handleVerifyMessage} className="verify-message-form">
            <div className="form-group">
              <label htmlFor="verify-address">Address</label>
              <input
                type="text"
                id="verify-address"
                value={verifyAddress}
                onChange={(e) => setVerifyAddress(e.target.value)}
                placeholder="Enter the signer's address"
                disabled={verifying}
                required
                className="full-width-input"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="verify-message">Message</label>
              <textarea
                id="verify-message"
                value={verifyMessage}
                onChange={(e) => setVerifyMessage(e.target.value)}
                placeholder="Enter the original message"
                rows={4}
                disabled={verifying}
                required
                className="full-width-input"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="verify-signature">Signature</label>
              <textarea
                id="verify-signature"
                value={verifySignature}
                onChange={(e) => setVerifySignature(e.target.value)}
                placeholder="Enter the signature to verify"
                rows={2}
                disabled={verifying}
                required
                className="full-width-input"
              />
            </div>
            
            <button
              type="submit"
              className="verify-button"
              disabled={verifying || !verifyAddress || !verifyMessage || !verifySignature}
            >
              {verifying ? 'Verifying...' : 'Verify Message'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default SignMessageSection; 