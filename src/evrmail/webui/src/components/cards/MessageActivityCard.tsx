import React from 'react';
import { callBackend } from '../../utils/bridge';

interface Message {
  id: string;
  sender: string;
  timestamp: number;
  subject: string;
  content: string;
  read: boolean;
}

interface MessageActivityCardProps {
  messages: Message[];
  backend: Backend | null;
}

const MessageActivityCard: React.FC<MessageActivityCardProps> = ({ messages, backend }) => {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    
    // If today, show time only
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    }
    
    // Otherwise show date
    return date.toLocaleDateString();
  };
  
  const handleMessageClick = async (messageId: string) => {
    if (!backend || !messageId) return;
    
    try {
      // Mark the message as read
      await callBackend(backend, 'mark_message_read', messageId);
      
      // Here you would typically navigate to the message detail view
      // or open it in a modal, etc.
      console.log(`Message ${messageId} marked as read`);
    } catch (err) {
      console.error('Error marking message as read:', err);
    }
  };
  
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recent Messages</h3>
      </div>
      <div className="dashboard-card-content">
        {messages.length === 0 ? (
          <div className="empty-state">No messages yet</div>
        ) : (
          <div className="message-activity-list">
            {messages.slice(0, 5).map(message => (
              <div 
                key={message.id} 
                className={`message-item-preview ${message.read ? '' : 'unread'}`}
                onClick={() => handleMessageClick(message.id)}
              >
                <div className="message-preview-content">
                  <div className="message-sender-preview">{message.sender}</div>
                  <div className="message-subject-preview">{message.subject}</div>
                </div>
                <div className="message-date-preview">
                  {formatDate(message.timestamp)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="dashboard-card-footer">
        <button className="view-all-button">View All Messages</button>
      </div>
    </div>
  );
};

export default MessageActivityCard; 