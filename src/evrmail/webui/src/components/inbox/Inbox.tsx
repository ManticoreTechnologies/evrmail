import React, { useState, useEffect } from 'react';
// @ts-ignore
import { getMessages, getFromBackend, callBackend } from '../../utils/bridge';
import type { Message } from '../../types/message';
import './Inbox.css';
import MessageList from './MessageList';
import MessageDetail from './MessageDetail';

interface InboxProps {
  backend: Backend | null;
}

const Inbox: React.FC<InboxProps> = ({ backend }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch messages
  useEffect(() => {
    const fetchMessages = async () => {
      if (!backend) {
        setError('Backend not available');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const fetchedMessages = await getMessages(backend);
        setMessages(fetchedMessages || []);
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching messages:', err);
        setError('Failed to load messages. Please try again.');
        setIsLoading(false);
      }
    };

    fetchMessages();
  }, [backend]);

  // Filter and search messages
  const filteredMessages = messages
    .filter(msg => filter === 'all' || (filter === 'unread' && !msg.read))
    .filter(msg => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        msg.subject.toLowerCase().includes(query) ||
        msg.sender.toLowerCase().includes(query) ||
        msg.content.toLowerCase().includes(query)
      );
    })
    // Sort by timestamp (newest first)
    .sort((a, b) => b.timestamp - a.timestamp);

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

  // Handle selecting a message
  const handleSelectMessage = (message: Message) => {
    setSelectedMessage(message);
    if (!message.read) {
      handleMarkAsRead(message.id);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-state">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-icon">⚠️</div>
        <div className="empty-title">Error</div>
        <div className="empty-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="inbox-container">
      <div className="search-filter-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search messages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select
          className="filter-dropdown"
          value={filter}
          onChange={(e) => setFilter(e.target.value as 'all' | 'unread')}
        >
          <option value="all">All Messages</option>
          <option value="unread">Unread Only</option>
        </select>
      </div>

      <div className="inbox-split-view">
        <MessageList
          messages={filteredMessages}
          selectedId={selectedMessage?.id}
          onSelectMessage={handleSelectMessage}
        />

        <MessageDetail
          message={selectedMessage}
          onDelete={handleDeleteMessage}
        />
      </div>
    </div>
  );
};

export default Inbox; 