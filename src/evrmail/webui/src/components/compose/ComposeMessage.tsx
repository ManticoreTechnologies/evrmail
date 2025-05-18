import React, { useState, useEffect } from 'react';
// @ts-ignore
import { callBackend, getFromBackend } from '../../utils/bridge';
// @ts-ignore
import type { OutgoingMessage, MessageSendResult } from '../../types/message';
import type { Contact, OutboxAsset } from '../../types/contact';
import './ComposeMessage.css';

interface ComposeMessageProps {
  backend: Backend | null;
  initialRecipient?: string;
  initialSubject?: string;
  initialContent?: string;
  onMessageSent?: () => void;
  onCancel?: () => void;
}

const ComposeMessage: React.FC<ComposeMessageProps> = ({
  backend,
  initialRecipient = '',
  initialSubject = '',
  initialContent = '',
  onMessageSent,
  onCancel
}) => {
  // Form state
  const [recipient, setRecipient] = useState(initialRecipient);
  const [subject, setSubject] = useState(initialSubject);
  const [messageContent, setMessageContent] = useState(initialContent);
  
  // Message sending state
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  
  // Contacts data
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [showContactsDropdown, setShowContactsDropdown] = useState(false);
  
  // Outbox assets
  const [outboxAssets, setOutboxAssets] = useState<OutboxAsset[]>([]);
  const [selectedOutbox, setSelectedOutbox] = useState('');
  const [customOutbox, setCustomOutbox] = useState(false);
  
  // State to track window height
  const [windowHeight, setWindowHeight] = useState(window.innerHeight);
  
  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const dropdown = document.querySelector('.contact-dropdown');
      const button = document.querySelector('.contact-list-button');
      
      if (dropdown && !dropdown.contains(event.target as Node) && 
          button && !button.contains(event.target as Node)) {
        setShowContactsDropdown(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setWindowHeight(window.innerHeight);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Load contacts and outbox assets
  useEffect(() => {
    if (!backend) return;
    
    const loadData = async () => {
      try {
        // Load contacts
        const contactsData = await getFromBackend<Contact[]>(backend, 'get_contacts');
        console.log('Contacts data:', contactsData);
        
        if (Array.isArray(contactsData)) {
          setContacts(contactsData);
        } else {
          // If it's an object with keys as addresses, convert to array
          if (contactsData && typeof contactsData === 'object') {
            const contactsArray = Object.entries(contactsData).map(([address, info]: [string, any]) => ({
              address,
              name: info.name || info.friendly_name || 'Unnamed',
              verified: !!info.verified,
              pubkey: info.pubkey
            }));
            setContacts(contactsArray);
          } else {
            setContacts([]);
          }
        }
        
        // Load wallet data to get assets
        const walletInfo = await getFromBackend<any>(backend, 'get_wallet_info');
        
        if (walletInfo && walletInfo.balances && walletInfo.balances.assets) {
          const assets: OutboxAsset[] = [];
          
          try {
            // Format assets into a usable format
            Object.entries(walletInfo.balances.assets).forEach(([address, assetInfo]: [string, any]) => {
              if (assetInfo && typeof assetInfo === 'object') {
                Object.entries(assetInfo).forEach(([assetName, balance]: [string, any]) => {
                  if (assetName !== 'EVR' && Number(balance) > 0) {
                    assets.push({
                      // @ts-ignore
                      name: assetName,
                      balance: Number(balance),
                      address: address
                    });
                  }
                });
              }
            });
            
            setOutboxAssets(assets);
            
            // Select the first asset by default if available
            if (assets.length > 0) {
              // @ts-ignore
              setSelectedOutbox(assets[0].name);
            }
          } catch (err) {
            console.error('Error processing wallet assets:', err);
          }
        }
      } catch (err) {
        console.error('Error loading data:', err);
        setStatus({
          type: 'error',
          message: 'Failed to load contacts or wallet data.'
        });
      }
    };
    
    loadData();
  }, [backend]);
  
  // Handle sending the message
  const handleSendMessage = async () => {
    if (!backend) return;
    
    // Validate required fields
    if (!recipient) {
      setStatus({ type: 'error', message: 'Please enter a recipient address.' });
      return;
    }
    
    if (!subject) {
      setStatus({ type: 'error', message: 'Please enter a subject.' });
      return;
    }
    
    if (!messageContent) {
      setStatus({ type: 'error', message: 'Please enter a message.' });
      return;
    }
    
    setIsSending(true);
    setStatus(null);
    
    try {
      const result = await callBackend<MessageSendResult>(
        backend,
        'send_message',
        recipient,
        subject,
        messageContent,
        customOutbox ? selectedOutbox : '',
        false  // Not a dry run
      );
      
      if (result.success) {
        setStatus({
          type: 'success',
          message: `Message sent successfully! ${result.txid ? `Transaction ID: ${result.txid}` : ''}`
        });
        
        // Clear form after successful send
        setRecipient('');
        setSubject('');
        setMessageContent('');
        
        // Call the onMessageSent callback if provided
        if (onMessageSent) {
          onMessageSent();
        }
      } else {
        setStatus({
          type: 'error',
          message: `Failed to send message: ${result.error || 'Unknown error'}`
        });
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setStatus({
        type: 'error',
        message: 'An error occurred while sending the message. Please try again.'
      });
    } finally {
      setIsSending(false);
    }
  };
  
  // Handle contact selection
  const handleSelectContact = (contact: Contact) => {
    setRecipient(contact.address);
    setShowContactsDropdown(false);
  };
  
  // Filter contacts as user types
  const filteredContacts = Array.isArray(contacts) 
    ? contacts.filter(contact => {
        const searchTerm = recipient.toLowerCase();
        return (
          contact.address.toLowerCase().includes(searchTerm) ||
          (contact.name && contact.name.toLowerCase().includes(searchTerm))
        );
      })
    : [];
  
  // Handle cancel
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      // Clear form
      setRecipient('');
      setSubject('');
      setMessageContent('');
      setStatus(null);
    }
  };
  
  return (
    <div className="compose-container" style={{ width: '100%' }}>
      {isSending && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
      
      <div className="compose-header">
        <h2 className="compose-title">Compose New Message</h2>
        <p className="compose-subtitle">Send a new encrypted message over the Evrmore blockchain</p>
      </div>
      
      {status && (
        <div className={`status-message ${status.type}`}>
          {status.message}
        </div>
      )}
      
      <div className="compose-form">
        <div className="form-group">
          <label className="form-label" htmlFor="recipient">To:</label>
          <div className="recipient-field">
            <input
              type="text"
              id="recipient"
              className="form-input"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder="Enter recipient EVR address or contact name"
              autoComplete="off"
            />
            <div 
              className="contact-list-button"
              onClick={() => setShowContactsDropdown(!showContactsDropdown)}
            >
              👤
            </div>
          </div>
          
          {showContactsDropdown && (
            <div className="contact-dropdown">
              {Array.isArray(filteredContacts) && filteredContacts.length > 0 ? (
                filteredContacts.map((contact) => (
                  <div 
                    key={contact.address}
                    className="contact-dropdown-item"
                    onClick={() => handleSelectContact(contact)}
                  >
                    <div className="contact-name">{contact.name || 'Unnamed'}</div>
                    <div className="contact-address">{contact.address}</div>
                  </div>
                ))
              ) : (
                <div className="contact-dropdown-item">
                  {Array.isArray(contacts) && contacts.length > 0 
                    ? 'No matching contacts found' 
                    : 'No contacts available'}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="form-group">
          <label className="form-label" htmlFor="subject">Subject:</label>
          <input
            type="text"
            id="subject"
            className="form-input"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Enter message subject"
          />
        </div>
        
        <div className="form-group" style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          minHeight: windowHeight < 700 ? '150px' : '300px' 
        }}>
          <label className="form-label" htmlFor="message">Message:</label>
          <textarea
            id="message"
            className="form-textarea"
            value={messageContent}
            onChange={(e) => setMessageContent(e.target.value)}
            placeholder="Type your message here..."
          />
        </div>
        
        <div className="outbox-section">
          <div className="outbox-heading">Message Sending Options</div>
          
          <div className="outbox-toggle">
            <input
              type="checkbox"
              id="custom-outbox"
              checked={customOutbox}
              onChange={() => setCustomOutbox(!customOutbox)}
            />
            <label htmlFor="custom-outbox" className="outbox-toggle-label">
              Specify custom outbox asset (advanced)
            </label>
          </div>
          
          {customOutbox && (
            <div className="outbox-selector">
              <label className="form-label" htmlFor="outbox">Outbox Asset:</label>
              <select
                id="outbox"
                className="form-select"
                value={selectedOutbox}
                onChange={(e) => setSelectedOutbox(e.target.value)}
                disabled={outboxAssets.length === 0}
              >
                <option value="">Select an asset</option>
                {outboxAssets.map((asset) => (
                  // @ts-ignore
                  <option key={asset.name} value={asset.name}>
                    {/* @ts-ignore */}
                    {asset.name} ({asset.balance} units)
                  </option>
                ))}
              </select>
              <p className="outbox-info">
                The message will be sent using the selected asset. 
                Make sure the asset has enough units (min 576).
              </p>
            </div>
          )}
        </div>
        
        <div className="form-actions">
          <button 
            className="btn btn-secondary"
            onClick={handleCancel}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary"
            disabled={isSending || !recipient || !subject || !messageContent || (customOutbox && !selectedOutbox)}
            onClick={handleSendMessage}
          >
            {isSending ? 'Sending...' : 'Send Message'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComposeMessage; 