import React from 'react';

const NAV_ITEMS = [
  ['dashboard', 'Dashboard'],
  ['live-view', 'Live View'],
  ['zones', 'Zones'],
  ['events', 'Events'],
  ['cameras', 'Cameras'],
  ['analytics', 'Analytics'],
  ['reports', 'Reports'],
  ['settings', 'Settings'],
];

const Sidebar = ({ currentPage, onNavigate }) => {
  return (
    <div className="sidebar-nav">
      <div className="sidebar-brand">
        <div className="brand-mark">S</div>
        <div>
          <div className="brand-name">Sentinel</div>
          <div className="brand-subtitle">Command Center</div>
        </div>
      </div>
      <ul>
        {NAV_ITEMS.map(([page, label]) => (
          <li key={page} className={currentPage === page ? 'active' : ''}>
            <button type="button" onClick={() => onNavigate(page)}>
              {label}
            </button>
          </li>
        ))}
      </ul>
      <div className="sidebar-footer">
        <span className="status-dot" />
        <span>Pipeline online</span>
      </div>
    </div>
  );
};

export default Sidebar;

