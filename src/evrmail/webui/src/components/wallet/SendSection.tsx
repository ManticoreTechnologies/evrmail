import React, { useState } from 'react';
import { sendEVR } from '../../utils/bridge';

interface SendSectionProps {
  backend: Backend | null;
  balances: {
    total_evr: number;
    evr: Record<string, number>;
  } | null;
  onTransactionSent: () => void;
}

const SendSection: React.FC<SendSectionProps> = ({ backend, balances, onTransactionSent }) => {
  const [recipientAddress, setRecipientAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [dryRun, setDryRun] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [txid, setTxid] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  // Get available balance
  const availableBalance = balances ? balances.total_evr : 0;

  // Validate inputs
  const validateInputs = (): boolean => {
    if (!recipientAddress.trim()) {
      setError('Please enter a recipient address');
      return false;
    }

    if (!amount.trim()) {
      setError('Please enter an amount to send');
      return false;
    }

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Please enter a valid amount greater than 0');
      return false;
    }

    if (parsedAmount > availableBalance) {
      setError(`Insufficient balance. Available: ${availableBalance} EVR`);
      return false;
    }

    return true;
  };

  // Handle sending EVR
  const handleSendEVR = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset states
    setError(null);
    setSuccess(null);
    setTxid(null);
    
    // Validate inputs
    if (!validateInputs()) {
      return;
    }
    
    // Send transaction
    setSending(true);
    
    try {
      if (!backend) {
        throw new Error('Backend not available');
      }
      
      const result = await sendEVR(
        backend,
        recipientAddress.trim(),
        parseFloat(amount),
        dryRun
      );
      
      if (result.success) {
        setSuccess(result.message || 'Transaction sent successfully');
        if (result.txid) {
          setTxid(result.txid);
        }
        
        if (!dryRun) {
          setRecipientAddress('');
          setAmount('');
          onTransactionSent();
        }
      } else {
        setError(result.error || 'Failed to send transaction');
      }
    } catch (err) {
      console.error('Error sending EVR:', err);
      setError('An error occurred while sending the transaction');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="send-section">
      <h2>Send EVR</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="success-message">
          {success}
          {txid && (
            <div className="txid-display">
              Transaction ID: <code>{txid}</code>
            </div>
          )}
        </div>
      )}
      
      <form onSubmit={handleSendEVR}>
        <div className="form-group">
          <label htmlFor="recipientAddress">Recipient Address</label>
          <input
            type="text"
            id="recipientAddress"
            value={recipientAddress}
            onChange={(e) => setRecipientAddress(e.target.value)}
            placeholder="Enter Evrmore address"
            disabled={sending}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="amount">Amount (EVR)</label>
          <div className="amount-input-container">
            <input
              type="number"
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00000000"
              step="0.00000001"
              min="0"
              max={availableBalance.toString()}
              disabled={sending}
            />
            {availableBalance > 0 && (
              <button
                type="button"
                className="max-button"
                onClick={() => setAmount(availableBalance.toString())}
                disabled={sending}
              >
                MAX
              </button>
            )}
          </div>
          <div className="balance-info">
            Available Balance: {availableBalance.toFixed(8)} EVR
          </div>
        </div>
        
        <div className="form-group checkbox-group">
          <label htmlFor="dryRun" className="checkbox-label">
            <input
              type="checkbox"
              id="dryRun"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              disabled={sending}
            />
            Dry run (simulate transaction without sending)
          </label>
        </div>
        
        <button
          type="submit"
          className="send-button"
          disabled={sending || !recipientAddress || !amount}
        >
          {sending ? 'Sending...' : dryRun ? 'Simulate Transaction' : 'Send EVR'}
        </button>
      </form>
    </div>
  );
};

export default SendSection; 