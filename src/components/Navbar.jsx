import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, Menu, User, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { mockNotifications } from '../data/mockData';
import Dropdown from './Dropdown';
import './Navbar.css';

export default function Navbar({ onMenuClick, title }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifs, setShowNotifs] = useState(false);
  const unreadCount = mockNotifications.filter(n => !n.read).length;

  const profileItems = [
    { icon: User, label: 'Profile', onClick: () => navigate('/profile') },
    { icon: Settings, label: 'Settings', onClick: () => navigate('/settings') },
    { divider: true },
    { icon: LogOut, label: 'Logout', danger: true, onClick: () => { logout(); navigate('/login'); } },
  ];

  return (
    <header className="navbar">
      <div className="navbar__left">
        <button className="navbar__menu" onClick={onMenuClick} aria-label="Menu">
          <Menu size={20} />
        </button>
        {title && <h2 className="navbar__title">{title}</h2>}
      </div>

      <div className="navbar__center">
        <div className="navbar__search">
          <Search size={16} className="navbar__search-icon" />
          <input
            type="text"
            className="navbar__search-input"
            placeholder="Search... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <kbd className="navbar__kbd">⌘K</kbd>
        </div>
      </div>

      <div className="navbar__right">
        <div className="navbar__notif-wrapper">
          <button className="navbar__icon-btn" onClick={() => setShowNotifs(!showNotifs)} aria-label="Notifications">
            <Bell size={20} />
            {unreadCount > 0 && <span className="navbar__badge">{unreadCount}</span>}
          </button>
          {showNotifs && (
            <div className="navbar__notif-panel" onClick={() => setShowNotifs(false)}>
              <div className="navbar__notif-header">Notifications</div>
              {mockNotifications.map(n => (
                <div key={n.id} className={`navbar__notif-item ${!n.read ? 'navbar__notif-item--unread' : ''}`}>
                  <div className={`navbar__notif-dot navbar__notif-dot--${n.type}`} />
                  <div>
                    <div className="navbar__notif-title">{n.title}</div>
                    <div className="navbar__notif-msg">{n.message}</div>
                    <div className="navbar__notif-time">{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <Dropdown
          trigger={
            <div className="navbar__profile">
              <div className="navbar__avatar">{user?.fullName?.charAt(0) || 'U'}</div>
              <span className="navbar__user-name">{user?.fullName || 'User'}</span>
            </div>
          }
          items={profileItems}
          align="right"
        />
      </div>
    </header>
  );
}
