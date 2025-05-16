import React from 'react';
import type { Message } from '../../types/message';

interface MessageDetailProps {
  message: Message | null;
  onDelete: (messageId: string) => void;
}

const MessageDetail: React.FC<MessageDetailProps> = ({ message, onDelete }) => {
  // Format timestamp to full readable date/time
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Handle reply to message
  const handleReply = () => {
    // This would be implemented to open compose view with pre-filled reply info
    console.log('Reply to:', message?.id);
  };
  
  // Handle forward message
  const handleForward = () => {
    // This would be implemented to open compose view with pre-filled forward info
    console.log('Forward:', message?.id);
  };
  
  // If no message is selected, show empty state
  if (!message) {
    return (
      <div className="message-detail-container">
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <div className="empty-title">No message selected</div>
          <div className="empty-message">Select a message from the list to view its contents.</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="message-detail-container">
      <div className="message-detail-header">
        <h2 className="message-detail-subject">{message.subject || '(No subject)'}</h2>
        <div className="message-detail-meta">
          <div>
            <span className="message-detail-sender">{message.sender}</span>
          </div>
          <div>
            <span className="message-detail-time">{formatTimestamp(message.timestamp)}</span>
          </div>
        </div>
      </div>
      
      <div className="message-detail-content">
        {message.content.split('\n').map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
      
      <div className="message-detail-actions">
        <button className="action-button primary" onClick={handleReply}>
          Reply
        </button>
        <button className="action-button secondary" onClick={handleForward}>
          Forward
        </button>
        <button 
          className="action-button danger" 
          onClick={() => onDelete(message.id)}
          style={{ marginLeft: 'auto' }}
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default MessageDetail; 