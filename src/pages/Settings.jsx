import { useState } from 'react';
import { motion } from 'framer-motion';
import { Palette, Bell, Key, Shield, Trash2, Copy, RefreshCw, Plus, AlertTriangle } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import Modal from '../components/Modal';
import { mockApiKeys } from '../data/mockData';
import { useToast } from '../context/ToastContext';
import './Settings.css';

const tabs = [
  { id: 'general', label: 'General', icon: Palette },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'apikeys', label: 'API Keys', icon: Key },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'danger', label: 'Danger Zone', icon: Trash2 },
];

function Toggle({ checked, onChange }) {
  return (
    <button className={`settings-toggle ${checked ? 'settings-toggle--on' : ''}`} onClick={() => onChange(!checked)}>
      <span className="settings-toggle__thumb" />
    </button>
  );
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [notifs, setNotifs] = useState({ email: true, completed: true, failed: true, digest: false, updates: true });
  const [deleteModal, setDeleteModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const toast = useToast();

  return (
    <motion.div className="settings-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header"><div><h1 className="page-header__title">Settings</h1><p className="page-header__subtitle">Manage your preferences</p></div></div>

      <div className="settings-layout">
        <nav className="settings-tabs">
          {tabs.map(tab => (
            <button key={tab.id} className={`settings-tab ${activeTab === tab.id ? 'settings-tab--active' : ''}`} onClick={() => setActiveTab(tab.id)}>
              <tab.icon size={16} /> {tab.label}
            </button>
          ))}
        </nav>

        <div className="settings-content">
          {activeTab === 'general' && (
            <Card>
              <h3 className="settings-section-title">General</h3>
              <div className="settings-row"><span>Theme</span><select className="pl-select"><option>Dark</option><option>Light</option><option>System</option></select></div>
              <div className="settings-row"><span>Language</span><select className="pl-select"><option>English</option></select></div>
              <div className="settings-row"><span>Timezone</span><select className="pl-select"><option>UTC+5:30 (IST)</option><option>UTC (GMT)</option><option>UTC-5 (EST)</option></select></div>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <h3 className="settings-section-title">Notifications</h3>
              {[
                ['email', 'Email Notifications'], ['completed', 'Test Run Completed'], ['failed', 'Test Run Failed'], ['digest', 'Weekly Digest'], ['updates', 'Agent Updates'],
              ].map(([key, label]) => (
                <div className="settings-row" key={key}>
                  <span>{label}</span>
                  <Toggle checked={notifs[key]} onChange={v => setNotifs(p => ({ ...p, [key]: v }))} />
                </div>
              ))}
            </Card>
          )}

          {activeTab === 'apikeys' && (
            <Card padding="none">
              <div style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
                <h3 className="settings-section-title" style={{ margin: 0 }}>API Keys</h3>
                <Button variant="primary" size="sm" leftIcon={Plus}>Generate New</Button>
              </div>
              <table className="dash-table" style={{ width: '100%' }}>
                <thead><tr><th>Name</th><th>Key</th><th>Created</th><th>Last Used</th><th>Actions</th></tr></thead>
                <tbody>
                  {mockApiKeys.map(k => (
                    <tr key={k.id}>
                      <td style={{ fontWeight: 500 }}>{k.name}</td>
                      <td><code style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{k.key}</code></td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>{k.created}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>{k.lastUsed}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <Button variant="ghost" size="sm" leftIcon={Copy} onClick={() => toast.success('API key copied!')} />
                          <Button variant="ghost" size="sm" leftIcon={RefreshCw} />
                          <Button variant="danger-ghost" size="sm" leftIcon={Trash2} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)' }}>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 6 }}><AlertTriangle size={14} /> API keys provide full access to your account. Keep them secret.</p>
              </div>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <h3 className="settings-section-title">Security</h3>
              <div className="settings-row"><span>Two-Factor Authentication</span><Toggle checked={false} onChange={() => toast.info('2FA settings coming soon')} /></div>
              <div className="settings-row"><span>Active Sessions</span><span style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>1 active session</span></div>
            </Card>
          )}

          {activeTab === 'danger' && (
            <Card className="settings-danger">
              <h3 className="settings-section-title" style={{ color: 'var(--danger)' }}>Danger Zone</h3>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 16 }}>Once you delete your account, there is no going back. Please be certain.</p>
              <Button variant="danger" leftIcon={Trash2} onClick={() => setDeleteModal(true)}>Delete Account</Button>
            </Card>
          )}
        </div>
      </div>

      <Modal isOpen={deleteModal} onClose={() => { setDeleteModal(false); setDeleteConfirm(''); }} title="Delete Account" size="sm" footer={
        <><Button variant="ghost" onClick={() => setDeleteModal(false)}>Cancel</Button><Button variant="danger" disabled={deleteConfirm !== 'DELETE'} onClick={() => { setDeleteModal(false); toast.error('Account deleted'); }}>Delete Account</Button></>
      }>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', marginBottom: 16 }}>This will permanently delete your account and all data. Type <strong>DELETE</strong> to confirm.</p>
        <Input placeholder="Type DELETE" value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)} />
      </Modal>
    </motion.div>
  );
}
