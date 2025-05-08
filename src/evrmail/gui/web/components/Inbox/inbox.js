import { loadTemplate } from '../../utils.js';

// Inbox view implementation
export async function initInboxView() {
  await loadTemplate('components/Inbox/inbox.html', 'inbox-view');
  
  // Set up event listeners
  document.getElementById('refresh-inbox').addEventListener('click', loadMessages);
  const searchInput = document.getElementById('inbox-search');
  searchInput.addEventListener('input', filterMessages);
  document.getElementById('inbox-search-clear').addEventListener('click', () => {
    searchInput.value = '';
    filterMessages();
  });
  
  // Load messages
  loadMessages();
}

// Add a global refresh function that app.js can call
export function refreshInbox() {
  // Check if the inbox view has been initialized
  const statusElement = document.getElementById('inbox-status');
  if (!statusElement) {
    // Initialize inbox view first if elements don't exist yet
    const container = document.getElementById('inbox-view');
    if (container) {
      // Create inbox container if it doesn't exist
      if (!document.getElementById('inbox-container')) {
        const inboxContainer = document.createElement('div');
        inboxContainer.id = 'inbox-container';
        container.appendChild(inboxContainer);
      }
      // Initialize the view
      initInboxView();
    }
  }
  
  // Now load messages
  loadMessages();
}

// Load messages from backend
function loadMessages() {
  const statusElement = document.getElementById('inbox-status');
  const messageList = document.getElementById('message-list');
  
  // Check if elements exist before proceeding
  if (!statusElement || !messageList) {
    console.error('Inbox elements not found. View may not be initialized.');
    return;
  }
  
  // Show loading status
  statusElement.className = 'alert alert-info';
  statusElement.textContent = 'Loading messages...';
  statusElement.style.display = 'block';
  
  // Clear current messages
  messageList.innerHTML = '';
  
  // Reset message details
  document.getElementById('message-header').textContent = 'Select a message to view';
  document.getElementById('message-details').innerHTML = '<p class="text-muted">No message selected</p>';
  document.getElementById('message-actions').classList.add('d-none');
  
  // Get messages from backend
  eel.get_messages()().then(messages => {
    if (messages && messages.length > 0) {
      // Hide status when messages are loaded
      statusElement.style.display = 'none';
      
      // Sort messages by timestamp (newest first)
      messages.sort((a, b) => b.timestamp - a.timestamp);
      
      // Store messages for filtering
      window.inboxMessages = messages;
      
      // Display messages
      renderMessageList(messages);
    } else {
      // Show empty inbox message
      statusElement.className = 'alert alert-secondary';
      statusElement.textContent = 'Your inbox is empty.';
    }
  }).catch(error => {
    console.error('Error loading messages:', error);
    statusElement.className = 'alert alert-danger';
    statusElement.textContent = 'Error loading messages. Please try again.';
  });
}

// Render message list
function renderMessageList(messages) {
  const messageList = document.getElementById('message-list');
  messageList.innerHTML = '';
  
  messages.forEach((message, index) => {
    const item = document.createElement('a');
    item.href = '#';
    item.className = 'list-group-item list-group-item-action';
    item.dataset.messageId = index;
    
    // Format date
    const date = new Date(message.timestamp * 1000);
    const formattedDate = date.toLocaleDateString();
    
    // Truncate subject if too long
    const subject = message.subject.length > 30 
      ? message.subject.substring(0, 27) + '...' 
      : message.subject;
    
    // Create item content
    item.innerHTML = `
      <div class="d-flex w-100 justify-content-between">
        <h5 class="mb-1">${escapeHtml(subject)}</h5>
        <small>${formattedDate}</small>
      </div>
      <p class="mb-1">From: ${escapeHtml(message.sender)}</p>
    `;
    
    // Set unread style
    if (!message.read) {
      item.classList.add('fw-bold');
    }
    
    // Add click event
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Remove active class from all items
      document.querySelectorAll('#message-list a').forEach(el => {
        el.classList.remove('active');
      });
      
      // Add active class to clicked item
      item.classList.add('active');
      
      // Remove bold style when read
      item.classList.remove('fw-bold');
      
      // Display message content
      displayMessage(index);
      
      // Mark as read in our UI
      window.inboxMessages[index].read = true;
      
      // Call backend to mark as read
      eel.mark_message_read(message.id)().catch(error => {
        console.error('Error marking message as read:', error);
      });
    });
    
    messageList.appendChild(item);
  });
}

// Display message content
function displayMessage(index) {
  const message = window.inboxMessages[index];
  const header = document.getElementById('message-header');
  const details = document.getElementById('message-details');
  const actions = document.getElementById('message-actions');
  
  // Set header
  header.textContent = escapeHtml(message.subject);
  
  // Format date
  const date = new Date(message.timestamp * 1000);
  const formattedDate = date.toLocaleString();
  
  // Set details
  details.innerHTML = `
    <div class="mb-3">
      <strong>From:</strong> ${escapeHtml(message.sender)}<br>
      <strong>Date:</strong> ${formattedDate}<br>
      <strong>Subject:</strong> ${escapeHtml(message.subject)}
    </div>
    <div class="message-body">
      ${formatMessageBody(message.content)}
    </div>
  `;
  
  // Show actions
  actions.classList.remove('d-none');
  
  // Set up reply button
  const replyButton = document.getElementById('reply-button');
  replyButton.onclick = () => {
    // Navigate to compose view with pre-filled data
    showView('compose');
    
    // Slight delay to ensure compose view is initialized
    setTimeout(() => {
      document.getElementById('recipient').value = message.sender;
      document.getElementById('subject').value = `Re: ${message.subject}`;
      document.getElementById('message').value = `\n\n-------- Original Message --------\nFrom: ${message.sender}\nDate: ${formattedDate}\nSubject: ${message.subject}\n\n${message.content}`;
      
      // Focus on message field
      document.getElementById('message').focus();
    }, 100);
  };
  
  // Set up delete button
  const deleteButton = document.getElementById('delete-button');
  deleteButton.onclick = () => {
    if (confirm('Are you sure you want to delete this message?')) {
      eel.delete_message(message.id)().then(result => {
        if (result.success) {
          // Remove from UI
          const messageItems = document.querySelectorAll('#message-list a');
          messageItems[index].remove();
          
          // Remove from stored messages
          window.inboxMessages.splice(index, 1);
          
          // Reset message details
          document.getElementById('message-header').textContent = 'Select a message to view';
          document.getElementById('message-details').innerHTML = '<p class="text-muted">No message selected</p>';
          document.getElementById('message-actions').classList.add('d-none');
          
          // Show empty inbox message if no messages left
          if (window.inboxMessages.length === 0) {
            const statusElement = document.getElementById('inbox-status');
            statusElement.className = 'alert alert-secondary';
            statusElement.textContent = 'Your inbox is empty.';
            statusElement.style.display = 'block';
          }
        } else {
          alert(`Error deleting message: ${result.error}`);
        }
      }).catch(error => {
        console.error('Error deleting message:', error);
        alert('Failed to delete message. Please try again.');
      });
    }
  };
}

// Filter messages by search term
function filterMessages() {
  const searchTerm = document.getElementById('inbox-search').value.toLowerCase();
  
  // Skip if no messages or empty search
  if (!window.inboxMessages) return;
  
  if (!searchTerm) {
    // Show all messages if search is empty
    renderMessageList(window.inboxMessages);
    return;
  }
  
  // Filter messages by sender, subject or content
  const filtered = window.inboxMessages.filter(message => {
    return message.sender.toLowerCase().includes(searchTerm) ||
           message.subject.toLowerCase().includes(searchTerm) ||
           message.content.toLowerCase().includes(searchTerm);
  });
  
  // Update status if no results
  const statusElement = document.getElementById('inbox-status');
  if (filtered.length === 0) {
    statusElement.className = 'alert alert-secondary';
    statusElement.textContent = 'No messages match your search.';
    statusElement.style.display = 'block';
  } else {
    statusElement.style.display = 'none';
  }
  
  // Render filtered list
  renderMessageList(filtered);
}

// Format message body with paragraphs and links
function formatMessageBody(content) {
  if (!content) return '';
  
  // Escape HTML first
  let escapedContent = escapeHtml(content);
  
  // Convert URLs to links
  escapedContent = escapedContent.replace(
    /(https?:\/\/[^\s]+)/g, 
    '<a href="$1" target="_blank">$1</a>'
  );
  
  // Convert line breaks to paragraphs
  return escapedContent.split('\n\n')
    .map(paragraph => `<p>${paragraph.replace(/\n/g, '<br>')}</p>`)
    .join('');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize on DOMContentLoaded if not loaded by app.js
document.addEventListener('DOMContentLoaded', function() {
  // Only initialize if not already initialized by app.js
  if (document.getElementById('inbox-container') && 
      !document.getElementById('inbox-container').innerHTML.trim()) {
    initInboxView();
  }
}); 