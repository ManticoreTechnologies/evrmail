import React from 'react';
// @ts-ignore
import type { Contact } from '../../types/contact';

interface ContactListProps {
  contacts: Record<string, any>;
  onRemoveContact: (address: string) => void;
  loading: boolean;
}

const ContactList: React.FC<ContactListProps> = ({ contacts, onRemoveContact, loading }) => {
  if (loading) {
    return <div className="loading">Loading contacts...</div>;
  }

  if (Object.keys(contacts).length === 0) {
    return (
      <div className="empty-state">
        <p>No contacts found.</p>
        <p>Add a contact using the form on the right.</p>
      </div>
    );
  }

  // Get initial for avatar
  const getInitial = (name: string) => {
    return (name || '?').charAt(0).toUpperCase();
  };

  return (
    <div className="contact-list">
      <h2>Your Contacts</h2>
      
      {Object.entries(contacts).map(([address, info]) => {
        const name = (info as any).name || 'Unnamed';
        const verified = (info as any).verified || false;
        
        return (
          <div key={address} className="contact-item">
            <div className="contact-avatar">
              {getInitial(name)}
            </div>
            
            <div className="contact-details">
              <div className="contact-name">{name}</div>
              <div className="contact-address">{address}</div>
              <div className="contact-status">
                {verified ? (
                  <span className="verified">✓ Verified</span>
                ) : (
                  <span className="unverified">⚠️ Unverified</span>
                )}
              </div>
            </div>
            
            <div className="contact-actions">
              <button 
                className="action-button message-button"
                onClick={() => {
                  // This would navigate to compose with pre-filled recipient
                  console.log('Message contact:', address);
                  // Navigate to compose with this address
                }}
              >
                Message
              </button>
              
              <button 
                className="action-button remove-button"
                onClick={() => onRemoveContact(address)}
              >
                Remove
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ContactList; 