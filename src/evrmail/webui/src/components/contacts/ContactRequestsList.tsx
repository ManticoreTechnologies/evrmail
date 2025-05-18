import React from 'react';
// @ts-ignore
import type { ContactRequest } from '../../types/contact';

interface ContactRequestsListProps {
  contactRequests: Record<string, any>;
  onAccept: (address: string) => void;
  onReject: (address: string) => void;
  loading: boolean;
}

const ContactRequestsList: React.FC<ContactRequestsListProps> = ({ 
  contactRequests, 
  onAccept, 
  onReject, 
  loading 
}) => {
  if (loading) {
    return <div className="loading">Loading contact requests...</div>;
  }

  if (Object.keys(contactRequests).length === 0) {
    return null; // Don't render anything if no requests
  }

  return (
    <div className="contact-requests-list">
      <h2>Contact Requests</h2>
      
      {Object.entries(contactRequests).map(([address, info]) => {
        const name = (info as any).name || 'Unnamed';
        
        return (
          <div key={address} className="contact-request-item">
            <div className="contact-request-details">
              <div className="contact-name">{name}</div>
              <div className="contact-address">{address}</div>
            </div>
            
            <div className="contact-request-actions">
              <button 
                className="action-button accept-button"
                onClick={() => onAccept(address)}
              >
                Accept
              </button>
              
              <button 
                className="action-button reject-button"
                onClick={() => onReject(address)}
              >
                Reject
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ContactRequestsList; 