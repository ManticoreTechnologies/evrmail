import React, { useEffect, useState } from 'react';
import './EvrMail.css';
import { getNetworkStatus, getMessages, getFromBackend, callBackend } from '../utils/bridge';

interface EvrMailProps {
  backend: Backend | null;
}

// Active view in the EvrMail component
type EvrMailView = 'dashboard' | 'inbox' | 'compose' | 'contacts' | 'wallet';

// Message interface
interface Message {
  id: string;
  sender: string;
  timestamp: number;
  subject: string;
  content: string;
  read: boolean;
}

// Contact interface
interface Contact {
  address: string;
  name: string;
  verified: boolean;
}

// Wallet interface
interface WalletBalance {
  total_evr: number;
  evr: Record<string, number>;
  assets: Record<string, Record<string, number>>;
}

const EvrMail: React.FC<EvrMailProps> = ({ backend }) => {
  const [appVersion, setAppVersion] = useState<string | null>(null);
  const [networkStatus, setNetworkStatus] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [activeView, setActiveView] = useState<EvrMailView>('dashboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Compose form state
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [messageContent, setMessageContent] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  
  // Selected message
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);

  useEffect(() => {
    // When EvrMail component mounts, fetch basic app info
    if (backend) {
      // Try to make sure browser is hidden safely
      try {
        if (backend.openTab && typeof backend.openTab === 'function') {
          backend.openTab('mail');
        } else {
          console.warn('Backend.openTab function not available');
        }
      } catch (err) {
        console.error('Error calling openTab:', err);
        setError('Error initializing UI components');
      }
      
      // Load initial data
      loadAppData();
    } else {
      setLoading(false);
      setError('Backend not available');
    }
  }, [backend]);

  const loadAppData = async () => {
    try {
      if (!backend) {
        setError('Backend not available');
        setLoading(false);
        return;
      }

      // Fetch app version
      try {
        const version = await getFromBackend<string>(backend, 'get_app_version');
        setAppVersion(version);
      } catch (err) {
        console.warn('Failed to get app version:', err);
      }
      
      // Fetch network status
      try {
        const status = await getNetworkStatus(backend);
        setNetworkStatus(status);
      } catch (err) {
        console.warn('Failed to get network status:', err);
      }
      
      // Fetch messages
      try {
        const msgs = await getMessages(backend);
        setMessages(msgs || []);
      } catch (err) {
        console.warn('Failed to get messages:', err);
      }
      
      // Fetch contacts
      try {
        const contacts = await getFromBackend<Contact[]>(backend, 'get_contacts');
        setContacts(contacts || []);
      } catch (err) {
        console.warn('Failed to get contacts:', err);
      }
      
      // Fetch wallet balances
      try {
        const balance = await getFromBackend<WalletBalance>(backend, 'get_wallet_balances');
        setWalletBalance(balance);
      } catch (err) {
        console.warn('Failed to get wallet balance:', err);
      }
    } catch (error) {
      console.error('Error loading app data:', error);
      setError('Failed to load application data');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle marking a message as read
  const handleMarkAsRead = async (messageId: string) => {
    if (!backend) return;
    
    try {
      await callBackend(backend, 'mark_message_read', messageId);
      // Update the messages list
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === messageId ? { ...msg, read: true } : msg
        )
      );
    } catch (err) {
      console.error('Error marking message as read:', err);
    }
  };
  
  // Handle deleting a message
  const handleDeleteMessage = async (messageId: string) => {
    if (!backend) return;
    
    try {
      await callBackend(backend, 'delete_message', messageId);
      // Remove the message from the list
      setMessages(prevMessages => 
        prevMessages.filter(msg => msg.id !== messageId)
      );
      // If the deleted message was selected, clear selection
      if (selectedMessage?.id === messageId) {
        setSelectedMessage(null);
      }
    } catch (err) {
      console.error('Error deleting message:', err);
    }
  };
  
  // Handle sending a message
  const handleSendMessage = async () => {
    if (!backend || !recipient || !subject || !messageContent) return;
    
    setSendingMessage(true);
    
    try {
      const result = await callBackend<{success: boolean, error?: string}>(
        backend, 
        'send_message', 
        recipient, 
        subject, 
        messageContent
      );
      
      if (result.success) {
        // Clear form
        setRecipient('');
        setSubject('');
        setMessageContent('');
        // Show dashboard
        setActiveView('dashboard');
      } else {
        setError(`Failed to send message: ${result.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setSendingMessage(false);
    }
  };
  
  // Render message list
  const renderMessageList = () => {
    if (!messages.length) {
      return <div className="empty-state">No messages in your inbox</div>;
    }
    
    return (
      <div className="message-list">
        {messages.map(message => (
          <div 
            key={message.id} 
            className={`message-item ${message.read ? 'read' : 'unread'} ${selectedMessage?.id === message.id ? 'selected' : ''}`}
            onClick={() => {
              setSelectedMessage(message);
              if (!message.read) {
                handleMarkAsRead(message.id);
              }
            }}
          >
            <div className="message-sender">{message.sender}</div>
            <div className="message-subject">{message.subject}</div>
            <div className="message-date">
              {new Date(message.timestamp * 1000).toLocaleString()}
            </div>
            <button 
              className="delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteMessage(message.id);
              }}
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    );
  };
  
  // Render message detail
  const renderMessageDetail = () => {
    if (!selectedMessage) {
      return <div className="empty-state">Select a message to view</div>;
    }
    
    return (
      <div className="message-detail">
        <div className="message-header">
          <h3>{selectedMessage.subject}</h3>
          <div className="message-info">
            <span>From: {selectedMessage.sender}</span>
            <span>Date: {new Date(selectedMessage.timestamp * 1000).toLocaleString()}</span>
          </div>
        </div>
        <div className="message-body">
          {selectedMessage.content}
        </div>
        <div className="message-actions">
          <button onClick={() => {
            setRecipient(selectedMessage.sender);
            setSubject(`Re: ${selectedMessage.subject}`);
            setMessageContent(`\n\n> ${selectedMessage.content.split('\n').join('\n> ')}`);
            setActiveView('compose');
          }}>Reply</button>
          <button onClick={() => handleDeleteMessage(selectedMessage.id)}>Delete</button>
        </div>
      </div>
    );
  };
  
  // Render contacts list
  const renderContacts = () => {
    if (!contacts.length) {
      return <div className="empty-state">No contacts yet</div>;
    }
    
    return (
      <div className="contacts-list">
        {contacts.map(contact => (
          <div key={contact.address} className="contact-item">
            <div className="contact-name">{contact.name || 'Unnamed'}</div>
            <div className="contact-address">{contact.address}</div>
            <div className="contact-status">
              {contact.verified ? '✓ Verified' : '⚠️ Unverified'}
            </div>
            <div className="contact-actions">
              <button onClick={() => {
                setRecipient(contact.address);
                setActiveView('compose');
              }}>
                Message
              </button>
              <button onClick={async () => {
                if (!backend) return;
                
                try {
                  await callBackend(backend, 'remove_contact', contact.address);
                  // Update contacts list
                  setContacts(prevContacts => 
                    prevContacts.filter(c => c.address !== contact.address)
                  );
                } catch (err) {
                  console.error('Error removing contact:', err);
                }
              }}>
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  // Render wallet section
  const renderWallet = () => {
    if (!walletBalance) {
      return <div className="empty-state">Wallet information not available</div>;
    }
    
    return (
      <div className="wallet-section">
        <div className="wallet-balance">
          <h3>Total Balance</h3>
          <div className="balance-amount">{walletBalance.total_evr} EVR</div>
        </div>
        
        <div className="wallet-details">
          <h3>Wallet Details</h3>
          
          <div className="wallet-evr">
            <h4>EVR by Wallet</h4>
            {Object.entries(walletBalance.evr).map(([wallet, amount]) => (
              <div key={wallet} className="wallet-item">
                <span className="wallet-name">{wallet}</span>
                <span className="wallet-amount">{amount} EVR</span>
              </div>
            ))}
          </div>
          
          {Object.keys(walletBalance.assets).length > 0 && (
            <div className="wallet-assets">
              <h4>Assets</h4>
              {Object.entries(walletBalance.assets).map(([wallet, assets]) => (
                <div key={wallet} className="wallet-asset-group">
                  <h5>{wallet}</h5>
                  {Object.entries(assets).map(([asset, amount]) => (
                    <div key={asset} className="asset-item">
                      <span className="asset-name">{asset}</span>
                      <span className="asset-amount">{amount}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Render compose form
  const renderComposeForm = () => {
    return (
      <div className="compose-form">
        <h3>Compose New Message</h3>
        <div className="form-field">
          <label htmlFor="recipient">To:</label>
          <input 
            type="text" 
            id="recipient"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="Recipient's EVR address"
          />
        </div>
        <div className="form-field">
          <label htmlFor="subject">Subject:</label>
          <input 
            type="text" 
            id="subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Message subject"
          />
        </div>
        <div className="form-field">
          <label htmlFor="message">Message:</label>
          <textarea 
            id="message"
            value={messageContent}
            onChange={(e) => setMessageContent(e.target.value)}
            placeholder="Type your message here..."
            rows={10}
          />
        </div>
        <div className="form-actions">
          <button 
            className="cancel-btn"
            onClick={() => {
              setRecipient('');
              setSubject('');
              setMessageContent('');
              setActiveView('dashboard');
            }}
          >
            Cancel
          </button>
          <button 
            className="send-btn"
            disabled={!recipient || !subject || !messageContent || sendingMessage}
            onClick={handleSendMessage}
          >
            {sendingMessage ? 'Sending...' : 'Send Message'}
          </button>
        </div>
      </div>
    );
  };
  
  // Render the actual content based on the active view
  const renderContent = () => {
    switch (activeView) {
      case 'inbox':
        return (
          <div className="inbox-view">
            <div className="inbox-sidebar">
              {renderMessageList()}
            </div>
            <div className="inbox-content">
              {renderMessageDetail()}
            </div>
          </div>
        );
      case 'compose':
        return renderComposeForm();
      case 'contacts':
        return renderContacts();
      case 'wallet':
        return renderWallet();
      default:
        return (
          <div className="dashboard">
            <p>Welcome to EvrMail - Your secure messaging application on the Evrmore blockchain.</p>
            <p>Select an option from the menu to get started.</p>
            
            <div className="mail-stats">
              <div className="stat-box">
                <h3>Inbox</h3>
                <div className="stat-count">{messages?.length || 0}</div>
                <div className="stat-label">messages</div>
              </div>
              
              <div className="stat-box">
                <h3>Contacts</h3>
                <div className="stat-count">{contacts?.length || 0}</div>
                <div className="stat-label">contacts</div>
              </div>
              
              <div className="stat-box">
                <h3>Balance</h3>
                <div className="stat-count">{walletBalance?.total_evr || 0}</div>
                <div className="stat-label">EVR</div>
              </div>
            </div>
            
            <div className="action-buttons">
              <button 
                className="action-button"
                onClick={() => setActiveView('inbox')}  
              >
                <span className="icon">📥</span>
                Inbox
              </button>
              <button 
                className="action-button"
                onClick={() => setActiveView('compose')}
              >
                <span className="icon">✉️</span>
                Compose
              </button>
              <button 
                className="action-button"
                onClick={() => setActiveView('contacts')}
              >
                <span className="icon">👤</span>
                Contacts
              </button>
              <button 
                className="action-button"
                onClick={() => setActiveView('wallet')}
              >
                <span className="icon">💼</span>
                Wallet
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="evrmail-container">
      <div className="evrmail-header">
        <div className="evrmail-logo">
          <span className="mail-icon">📬</span>
          <h1>EvrMail</h1>
          {appVersion && <span className="version">v{appVersion}</span>}
        </div>
        {networkStatus && (
          <div className="network-status">
            <span className={`status-dot ${networkStatus.connected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">
              {networkStatus.connected 
                ? `Connected (${networkStatus.network || 'Unknown'})` 
                : 'Disconnected'}
            </span>
          </div>
        )}
        <div className="nav-buttons">
          <button 
            className={activeView === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveView('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={activeView === 'inbox' ? 'active' : ''}
            onClick={() => setActiveView('inbox')}
          >
            Inbox
          </button>
          <button 
            className={activeView === 'compose' ? 'active' : ''}
            onClick={() => setActiveView('compose')}
          >
            Compose
          </button>
          <button 
            className={activeView === 'contacts' ? 'active' : ''}
            onClick={() => setActiveView('contacts')}
          >
            Contacts
          </button>
          <button 
            className={activeView === 'wallet' ? 'active' : ''}
            onClick={() => setActiveView('wallet')}
          >
            Wallet
          </button>
        </div>
      </div>
      <div className="evrmail-content">
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}
        {loading ? (
          <div className="loading">Loading EvrMail...</div>
        ) : (
          renderContent()
        )}
      </div>
    </div>
  );
};

export default EvrMail; 