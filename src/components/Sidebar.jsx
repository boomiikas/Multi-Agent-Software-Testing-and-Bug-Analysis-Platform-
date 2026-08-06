import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Hexagon, LayoutDashboard, FolderKanban, Play, Terminal,
  FileText, Database, User, Settings, LogOut, PanelLeftClose,
  PanelLeft, X, UserCog
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/projects', icon: FolderKanban, label: 'Projects' },
  { path: '/run-monitor', icon: Play, label: 'Run Monitor' },
  { path: '/console', icon: Terminal, label: 'Console' },
  { path: '/success', icon: FileText, label: 'Reports' },
  { path: '/db-models', icon: Database, label: 'DB Models' },
];

// Shown only to ADMIN users, appended to the main nav section.
const adminNavItems = [
  { path: '/admin/users', icon: UserCog, label: 'Manage Users' },
];

const bottomItems = [
  { path: '/profile', icon: User, label: 'Profile' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const items = isAdmin ? [...navItems, ...adminNavItems] : navItems;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <>
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon"><Hexagon size={22} /></div>
          {!collapsed && <span className="sidebar__logo-text">AgentQA</span>}
        </div>
        <button className="sidebar__toggle" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      <nav className="sidebar__nav">
        <div className="sidebar__section">
          {!collapsed && <span className="sidebar__section-label">Main</span>}
          {items.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              onClick={onMobileClose}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        <div className="sidebar__section sidebar__section--bottom">
          {!collapsed && <span className="sidebar__section-label">Account</span>}
          {bottomItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              onClick={onMobileClose}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
          <button className="sidebar__link sidebar__link--danger" onClick={handleLogout} title={collapsed ? 'Logout' : undefined}>
            <LogOut size={20} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </nav>

      {!collapsed && user && (
        <div className="sidebar__user">
          <div className="sidebar__avatar">{user.fullName?.charAt(0)}</div>
          <div className="sidebar__user-info">
            <span className="sidebar__user-name">{user.fullName}</span>
            <span className="sidebar__user-email">{user.email}</span>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              className="sidebar-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onMobileClose}
            />
            <motion.aside
              className="sidebar sidebar--mobile"
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25 }}
            >
              <button className="sidebar__mobile-close" onClick={onMobileClose}>
                <X size={20} />
              </button>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
