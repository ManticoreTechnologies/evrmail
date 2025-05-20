import React from 'react';

interface ContactsCardProps {
  contacts: Record<string, {
    name: string;
    status: string;
    pubkey?: string;
  }> | null;
  backend: Backend | null;
}

const ContactsCard: React.FC<ContactsCardProps> = ({ contacts, backend }) => {
  // Get the first letter of a name for the avatar
  const getInitial = (name: string) => {
    return (name || '?').charAt(0).toUpperCase();
  };
  
  // Format contacts for display
  const getContactList = () => {
    if (!contacts) return [];
    
    return Object.entries(contacts)
      .map(([address, info]) => ({
        address,
        name: info.name || 'Unnamed',
        status: info.status || 'pending'
      }))
      .slice(0, 5); // Show only the first 5 contacts
  };
  
  // Check if we have pending contact requests
  // @ts-ignore
  const hasPendingRequests = async () => {
    if (!backend) return false;
    
    try {
      // This would be implemented in a real component
      // const requests = await getFromBackend(backend, 'get_contact_requests');
      // return Object.keys(requests).length > 0;
      return false;
    } catch (err) {
      console.error('Error checking contact requests:', err);
      return false;
    }
  };
  
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Contacts</h3>
      </div>
      <div className="dashboard-card-content">
        {getContactList().length === 0 ? (
          <div className="empty-state">No contacts yet</div>
        ) : (
          <div className="contacts-preview-list">
            {getContactList().map(contact => (
              <div key={contact.address} className="contact-preview-item">
                <div className="contact-avatar">
                  {getInitial(contact.name)}
                </div>
                <div className="contact-info">
                  <div className="contact-name">{contact.name}</div>
                  <div className="contact-address">{contact.address}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="dashboard-card-footer">
        <button className="add-contact-button">Add Contact</button>
      </div>
    </div>
  );
};

export default ContactsCard; 