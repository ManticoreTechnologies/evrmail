import React from 'react';

interface QuickActionsRowProps {
  backend: Backend | null;
}

const QuickActionsRow: React.FC<QuickActionsRowProps> = ({ backend }) => {
  // Define the available quick actions
  const quickActions = [
    {
      id: 'compose',
      label: 'Compose Message',
      icon: '✉️',
      action: () => {
        console.log('Compose message clicked');
        // Navigate to compose view or open compose modal
      }
    },
    {
      id: 'contacts',
      label: 'Add Contact',
      icon: '👤',
      action: () => {
        console.log('Add contact clicked');
        // Navigate to contacts view or open add contact modal
      }
    },
    {
      id: 'receive',
      label: 'Receive Address',
      icon: '📥',
      action: async () => {
        if (!backend) return;
        
        try {
          const result = await backend.generate_receive_address();
          console.log('Generated address:', JSON.parse(result));
          // Show the generated address in a modal or copy to clipboard
        } catch (err) {
          console.error('Error generating receive address:', err);
        }
      }
    },
    {
      id: 'send',
      label: 'Send EVR',
      icon: '💸',
      action: () => {
        console.log('Send EVR clicked');
        // Navigate to send view or open send modal
      }
    },
    {
      id: 'browser',
      label: 'Browse .evr',
      icon: '🌐',
      action: () => {
        // This would typically switch to the browser tab
        if (backend && backend.openTab) {
          backend.openTab('browser');
        }
      }
    }
  ];
  
  return (
    <div className="quick-actions-container">
      {quickActions.map(action => (
        <button 
          key={action.id}
          className="quick-action-button"
          onClick={action.action}
        >
          <div className="quick-action-icon">{action.icon}</div>
          <div className="quick-action-label">{action.label}</div>
        </button>
      ))}
    </div>
  );
};

export default QuickActionsRow; 