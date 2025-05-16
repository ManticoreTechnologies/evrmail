import React from 'react';
import type { Message } from '../../types/message';

interface MessageListProps {
  messages: Message[];
  selectedId: string | undefined;
  onSelectMessage: (message: Message) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, selectedId, onSelectMessage }) => {
  // Format timestamp to readable date/time
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    
    // If today, show time only
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    }
    
    // If this year, show month and day
    if (date.getFullYear() === now.getFullYear()) {
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }
    
    // Otherwise show date with year
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  };
  
  // Generate a preview of the message content (first 60 characters)
  const getContentPreview = (content: string) => {
    if (!content) return '';
    return content.length > 60 ? content.substring(0, 60) + '...' : content;
  };
  
  if (messages.length === 0) {
    return (
      <div className="message-list-container">
        <div className="message-list-header">
          <h3 className="message-list-title">Inbox</h3>
          <span className="message-count">0 messages</span>
        </div>
        <div className="empty-state">
          <div className="empty-icon">📩</div>
          <div className="empty-title">No messages</div>
          <div className="empty-message">Your inbox is empty.</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="message-list-container">
      <div className="message-list-header">
        <h3 className="message-list-title">Inbox</h3>
        <span className="message-count">{messages.length} message{messages.length !== 1 ? 's' : ''}</span>
      </div>
      <ul className="message-list">
        {messages.map((message) => {
          const isSelected = message.id === selectedId;
          const isUnread = !message.read;
          
          return (
            <li
              key={message.id}
              className={`message-list-item ${isSelected ? 'selected' : ''} ${isUnread ? 'unread' : ''}`}
              onClick={() => onSelectMessage(message)}
            >
              <div className="message-item-header">
                <span className="message-sender">{message.sender}</span>
                <span className="message-date">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="message-subject">{message.subject || '(No subject)'}</div>
              <div className="message-preview">{getContentPreview(message.content)}</div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default MessageList; 