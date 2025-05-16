import React from 'react';

interface Action {
  type: 'message' | 'transaction' | 'contact' | 'asset';
  description: string;
  timestamp: number;
  status: 'pending' | 'complete' | 'failed';
}

interface RecentActionsCardProps {
  actions: Action[];
}

const RecentActionsCard: React.FC<RecentActionsCardProps> = ({ actions }) => {
  // Format timestamp to readable date/time
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    
    // If today, show time only
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    }
    
    // Otherwise show date
    return date.toLocaleDateString();
  };
  
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recent Activity</h3>
      </div>
      <div className="dashboard-card-content">
        {actions.length === 0 ? (
          <div className="empty-state">No recent activity</div>
        ) : (
          <div className="actions-list">
            {actions.map((action, index) => (
              <div key={index} className="action-item">
                <div className="action-description">{action.description}</div>
                <div className="action-meta">
                  <span className="action-timestamp">{formatTimestamp(action.timestamp)}</span>
                  <span className={`action-status ${action.status}`}>{action.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentActionsCard; 