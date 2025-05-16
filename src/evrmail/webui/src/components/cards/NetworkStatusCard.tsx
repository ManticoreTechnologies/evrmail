import React from 'react';

interface NetworkStatusCardProps {
  networkStatus: {
    connected: boolean;
    network: string;
    peers: number;
    height: number;
  } | null;
}

const NetworkStatusCard: React.FC<NetworkStatusCardProps> = ({ networkStatus }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Network Status</h3>
      </div>
      <div className="dashboard-card-content">
        <div className="network-status-content">
          <div className="status-indicator">
            <div className={`status-dot ${networkStatus?.connected ? 'connected' : 'disconnected'}`}></div>
            <span>{networkStatus?.connected ? 'Connected' : 'Disconnected'}</span>
          </div>
          
          <div className="network-info">
            <div className="network-info-item">
              <span className="network-info-label">Network</span>
              <span className="network-info-value">{networkStatus?.network || 'Unknown'}</span>
            </div>
            
            <div className="network-info-item">
              <span className="network-info-label">Peers</span>
              <span className="network-info-value">{networkStatus?.peers || 0}</span>
            </div>
            
            <div className="network-info-item">
              <span className="network-info-label">Block Height</span>
              <span className="network-info-value">{networkStatus?.height || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkStatusCard; 