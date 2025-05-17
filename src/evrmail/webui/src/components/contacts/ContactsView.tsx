import React, { useState, useEffect } from 'react';
import { 
  getContacts, 
  getContactRequests,
  removeContact,
  acceptContactRequest,
  rejectContactRequest
} from '../../utils/bridge';
import ContactList from './ContactList';
import ContactRequestsList from './ContactRequestsList';
import AddContactForm from './AddContactForm';
import './Contacts.css';
import type { Contact, ContactRequest } from '../../types/contact';

interface ContactsViewProps {
  backend: Backend | null;
}

const ContactsView: React.FC<ContactsViewProps> = ({ backend }) => {
  const [contacts, setContacts] = useState<Record<string, any>>({});
  const [contactRequests, setContactRequests] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Load contacts and contact requests
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Load contacts
        const contactsData = await getContacts(backend);
        setContacts(contactsData || {});
        
        // Load contact requests
        const requestsData = await getContactRequests(backend);
        setContactRequests(requestsData || {});
      } catch (err) {
        console.error('Error loading contacts data:', err);
        setError('Failed to load contacts. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    if (backend) {
      loadData();
    }
  }, [backend, refreshTrigger]);

  // Handle contact removal
  const handleRemoveContact = async (address: string) => {
    if (!backend) return;
    
    try {
      const result = await removeContact(backend, address);
      
      if (result.success) {
        // Update local state
        const updatedContacts = { ...contacts };
        delete updatedContacts[address];
        setContacts(updatedContacts);
      } else {
        setError(result.error || 'Failed to remove contact');
      }
    } catch (err) {
      console.error('Error removing contact:', err);
      setError('An error occurred while removing the contact');
    }
  };

  // Handle accepting contact request
  const handleAcceptRequest = async (address: string) => {
    if (!backend) return;
    
    try {
      const result = await acceptContactRequest(backend, address);
      
      if (result.success) {
        // Refresh data
        setRefreshTrigger(prev => prev + 1);
      } else {
        setError(result.error || 'Failed to accept contact request');
      }
    } catch (err) {
      console.error('Error accepting contact request:', err);
      setError('An error occurred while accepting the contact request');
    }
  };

  // Handle rejecting contact request
  const handleRejectRequest = async (address: string) => {
    if (!backend) return;
    
    try {
      const result = await rejectContactRequest(backend, address);
      
      if (result.success) {
        // Update local state
        const updatedRequests = { ...contactRequests };
        delete updatedRequests[address];
        setContactRequests(updatedRequests);
      } else {
        setError(result.error || 'Failed to reject contact request');
      }
    } catch (err) {
      console.error('Error rejecting contact request:', err);
      setError('An error occurred while rejecting the contact request');
    }
  };

  // Filter contacts based on search term
  const filteredContacts = searchTerm 
    ? Object.entries(contacts).filter(([address, info]) => {
        const name = (info as any).name || '';
        return address.toLowerCase().includes(searchTerm.toLowerCase()) || 
               name.toLowerCase().includes(searchTerm.toLowerCase());
      }).reduce((obj, [key, value]) => {
        obj[key] = value;
        return obj;
      }, {} as Record<string, any>)
    : contacts;

  return (
    <div className="contacts-view">
      <h1>Contacts</h1>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="contacts-search">
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      
      <div className="contacts-container">
        <div className="contacts-main">
          <ContactList 
            contacts={filteredContacts} 
            onRemoveContact={handleRemoveContact}
            loading={loading}
          />
        </div>
        
        <div className="contacts-sidebar">
          {Object.keys(contactRequests).length > 0 && (
            <ContactRequestsList 
              contactRequests={contactRequests}
              onAccept={handleAcceptRequest}
              onReject={handleRejectRequest}
              loading={loading}
            />
          )}
          
          <AddContactForm 
            backend={backend}
            onContactAdded={() => setRefreshTrigger(prev => prev + 1)}
          />
        </div>
      </div>
    </div>
  );
};

export default ContactsView; 