import React from 'react';

interface QuickStatsCardProps {
  stats: {
    total: number;
    inbox: number;
    sent: number;
    unread: number;
  } | null;
  walletData: {
    balances: {
      total_evr: number;
    };
    addressCount: number;
  } | null;
}

const QuickStatsCard: React.FC<QuickStatsCardProps> = ({ stats, walletData }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Quick Stats</h3>
      </div>
      <div className="dashboard-card-content">
        <div className="quick-stats-grid">
          <div className="stat-item">
            <div className="stat-value">{stats?.unread || 0}</div>
            <div className="stat-label">Unread Messages</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{stats?.total || 0}</div>
            <div className="stat-label">Total Messages</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {walletData?.balances?.total_evr
                ? walletData.balances.total_evr.toFixed(4)
                : '0.0000'}
            </div>
            <div className="stat-label">EVR Balance</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{walletData?.addressCount || 0}</div>
            <div className="stat-label">Addresses</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickStatsCard; 