import React, { useState } from 'react';
import { sendContactRequest } from '../../utils/bridge';

interface AddContactFormProps {
  backend: Backend | null;
  onContactAdded: () => void;
}

const AddContactForm: React.FC<AddContactFormProps> = ({ backend, onContactAdded }) => {
  const [address, setAddress] = useState('');
  const [name, setName] = useState('');
  const [addressMode, setAddressMode] = useState('random');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!backend) {
      setError('Backend not available');
      return;
    }
    
    if (!address.trim()) {
      setError('Please enter a valid Evrmore address');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await sendContactRequest(
        backend,
        address.trim(),
        name.trim() || undefined,
        addressMode
      );
      
      if (result.success) {
        setSuccess('Contact request sent successfully');
        setAddress('');
        setName('');
        onContactAdded();
      } else {
        setError(result.error || 'Failed to send contact request');
      }
    } catch (err) {
      console.error('Error sending contact request:', err);
      setError('An error occurred while sending the contact request');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="add-contact-form">
      <h2>Add New Contact</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="address">Evrmore Address</label>
          <input
            type="text"
            id="address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Enter Evrmore address"
            disabled={isSubmitting}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="name">Name (optional)</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter contact name"
            disabled={isSubmitting}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="addressMode">Address Mode</label>
          <select
            id="addressMode"
            value={addressMode}
            onChange={(e) => setAddressMode(e.target.value)}
            disabled={isSubmitting}
          >
            <option value="random">Use Random Address</option>
            <option value="new">Generate New Address</option>
          </select>
          <small className="form-text">
            This determines which of your addresses will be used for this contact
          </small>
        </div>
        
        <button 
          type="submit" 
          className="submit-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Sending...' : 'Send Contact Request'}
        </button>
      </form>
    </div>
  );
};

export default AddContactForm; 