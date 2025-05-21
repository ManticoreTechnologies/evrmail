import React from 'react';

interface QuickActionsRowProps {
  backend: Backend | null;
  onNavigate: (view: string, params?: any) => void;
}

const QuickActionsRow: React.FC<QuickActionsRowProps> = ({ backend, onNavigate }) => {
  // Define the available quick actions
  const quickActions = [
    {
      id: 'compose',
      label: 'Compose Message',
      icon: '✉️',
      action: () => {
        console.log('Compose message clicked');
        onNavigate('compose');
      }
    },
    {
      id: 'contacts',
      label: 'Add Contact',
      icon: '👤',
      action: () => {
        console.log('Add contact clicked');
        onNavigate('contacts');
      }
    },
    {
      id: 'receive',
      label: 'Receive Address',
      icon: '📥',
      action: async () => {
        if (!backend) return;
        
        // First navigate to wallet view
        onNavigate('wallet');
        
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
        onNavigate('wallet');
      }
    },
    {
      id: 'browser',
      label: 'Browse .evr',
      icon: '🌐',
      action: () => {
        console.log('Browser clicked');
        onNavigate('browser');
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