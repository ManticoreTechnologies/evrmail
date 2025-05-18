import React, { useEffect, useState } from 'react';
import './EvrMail.css';
import { getNetworkStatus, getMessages, getFromBackend, callBackend } from '../utils/bridge';
import Dashboard from './Dashboard';
import Inbox from './inbox/Inbox';
import ComposeMessage from './compose/ComposeMessage';
import ContactsView from './contacts/ContactsView';
import WalletView from './wallet/WalletView';
// @ts-ignore
import ErrorBoundary from './ErrorBoundary';
import type { Message } from '../types/message';

interface EvrMailProps {
  backend: Backend | null;
}

// Active view in the EvrMail component
type EvrMailView = 'dashboard' | 'inbox' | 'compose' | 'contacts' | 'wallet';

// Message interface
// interface Message {
//   id: string;
//   sender: string;
//   timestamp: number;
//   subject: string;
//   content: string;
//   read: boolean;
// }

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
  // @ts-ignore
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [activeView, setActiveView] = useState<EvrMailView>('dashboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Compose form state
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [messageContent, setMessageContent] = useState(''); 
  // @ts-ignore
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
  // @ts-ignore
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
  // @ts-ignore
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
  // @ts-ignore
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
  
  // Render wallet section
  // @ts-ignore
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
  
  // Render the actual content based on the active view
  const renderContent = () => {
    if (loading) {
      return <div className="loading">Loading your data...</div>;
    }

    if (error) {
      return <div className="error">{error}</div>;
    }

    switch (activeView) {
      case 'dashboard':
        return (
          <Dashboard 
            backend={backend}
          />
        );
      case 'inbox':
        return (
          <Inbox 
            backend={backend}
          />
        );
      case 'compose':
        return (
          <ComposeMessage
            backend={backend}
            initialRecipient={recipient}
            initialSubject={subject}
            initialContent={messageContent}
            onMessageSent={() => {
              setRecipient('');
              setSubject('');
              setMessageContent('');
              setActiveView('dashboard');
            }}
            onCancel={() => setActiveView('dashboard')}
          />
        );
      case 'contacts':
        return (
          <ContactsView
            backend={backend}
          />
        );
      case 'wallet':
        return (
          <WalletView
            backend={backend}
          />
        );
      default:
        return <div>Unknown view</div>;
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
        {renderContent()}
      </div>
    </div>
  );
};

export default EvrMail; 