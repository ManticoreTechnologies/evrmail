import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import QuickStatsCard from './cards/QuickStatsCard';
import MessageActivityCard from './cards/MessageActivityCard';
import NetworkStatusCard from './cards/NetworkStatusCard';
import WalletOverviewCard from './cards/WalletOverviewCard';
import ContactsCard from './cards/ContactsCard';
import RecentActionsCard from './cards/RecentActionsCard';
import QuickActionsRow from './cards/QuickActionsRow';
import { getFromBackend, getNetworkStatus, getWalletBalances, getMessages } from '../utils/bridge';

interface DashboardProps {
  backend: Backend | null;
}

const Dashboard: React.FC<DashboardProps> = ({ backend }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [networkStatus, setNetworkStatus] = useState<any>(null);
  const [walletData, setWalletData] = useState<any>(null);
  const [contacts, setContacts] = useState<any>(null);
  const [recentActions, setRecentActions] = useState<any[]>([]);

  // Load all dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      if (!backend) {
        setError('Backend not available');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        
        // Fetch message stats
        try {
          const messageStats = await getFromBackend<any>(backend, 'get_message_stats');
          setStats(messageStats);
        } catch (err) {
          console.warn('Error fetching message stats:', err);
        }
        
        // Fetch recent messages
        try {
          const recentMessages = await getMessages(backend);
          setMessages(recentMessages || []);
        } catch (err) {
          console.warn('Error fetching messages:', err);
        }
        
        // Fetch network status
        try {
          const status = await getNetworkStatus(backend);
          setNetworkStatus(status);
        } catch (err) {
          console.warn('Error fetching network status:', err);
        }
        
        // Fetch wallet data
        try {
          const balances = await getWalletBalances(backend);
          const addresses = await getFromBackend<any[]>(backend, 'get_wallet_addresses');
          setWalletData({
            balances,
            addressCount: addresses?.length || 0,
            addresses
          });
        } catch (err) {
          console.warn('Error fetching wallet data:', err);
        }
        
        // Fetch contacts
        try {
          const contactsData = await getFromBackend<any>(backend, 'get_contacts');
          setContacts(contactsData);
        } catch (err) {
          console.warn('Error fetching contacts:', err);
        }
        
        // Create "recent actions" from sent messages and other activities
        try {
          const sentMessages = await getFromBackend<any[]>(backend, 'get_sent_messages');
          const actionsFromMessages = (sentMessages || []).slice(0, 5).map(msg => ({
            type: 'message',
            description: `Sent message to ${msg.to}: ${msg.subject}`,
            timestamp: new Date(msg.date).getTime(),
            status: 'complete'
          }));
          setRecentActions(actionsFromMessages);
        } catch (err) {
          console.warn('Error creating recent actions:', err);
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setError('Failed to load dashboard data. Please try again.');
        setIsLoading(false);
      }
    };
    
    loadDashboardData();
  }, [backend]);
  
  if (isLoading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="dashboard-error">
        <div className="error-icon">⚠️</div>
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Refresh</button>
      </div>
    );
  }
  
  return (
    <div className="dashboard-container">
      <div className="dashboard-row three-columns">
        <QuickStatsCard 
          stats={stats}
          walletData={walletData}
        />
        <MessageActivityCard 
          messages={messages}
          backend={backend}
        />
        <NetworkStatusCard 
          networkStatus={networkStatus}
        />
      </div>
      
      <div className="dashboard-row single-column">
        <WalletOverviewCard 
          walletData={walletData}
          backend={backend}
        />
      </div>
      
      <div className="dashboard-row two-columns">
        <ContactsCard 
          contacts={contacts}
          backend={backend}
        />
        <RecentActionsCard 
          actions={recentActions}
        />
      </div>
      
      <QuickActionsRow backend={backend} />
    </div>
  );
};

export default Dashboard; 