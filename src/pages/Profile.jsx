import { useState } from 'react';
import { motion } from 'framer-motion';
import { Camera, Moon, Sun, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import { useToast } from '../context/ToastContext';
import { userApi } from '../services/api';
import './Profile.css';

export default function Profile() {
  const { user, logout, setUser, changePassword } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const toast = useToast();
  const [fullName, setFullName] = useState(user?.fullName || '');
  const [savingProfile, setSavingProfile] = useState(false);
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [changingPw, setChangingPw] = useState(false);

  const handleSaveProfile = async () => {
    if (!fullName || fullName.trim().length < 2) { toast.error('Full name must be at least 2 characters'); return; }
    setSavingProfile(true);
    try {
      const { user: updated } = await userApi.updateProfile({ fullName });
      setUser(updated);
      toast.success('Profile updated successfully');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPw || !newPw) { toast.error('Fill in all password fields'); return; }
    if (newPw !== confirmPw) { toast.error('Passwords do not match'); return; }
    setChangingPw(true);
    const result = await changePassword(currentPw, newPw);
    setChangingPw(false);
    if (result.success) {
      toast.success('Password changed successfully');
      setCurrentPw(''); setNewPw(''); setConfirmPw('');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <motion.div className="profile-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header"><div><h1 className="page-header__title">Profile</h1><p className="page-header__subtitle">Manage your account</p></div></div>

      <Card className="profile-user-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar">{user?.fullName?.charAt(0) || 'U'}</div>
          <Button variant="ghost" size="sm" leftIcon={Camera}>Change Avatar</Button>
        </div>
        <div className="profile-fields">
          <Input label="Full Name" value={fullName} onChange={e => setFullName(e.target.value)} />
          <Input label="Email" type="email" value={user?.email || ''} disabled helperText="Email can't be changed here yet." />
          <div className="profile-meta">
            <span>Role: <strong>{user?.role || 'USER'}</strong></span>
            <span>Member since: <strong>{user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : '—'}</strong></span>
          </div>
          <Button variant="primary" loading={savingProfile} onClick={handleSaveProfile}>Save Changes</Button>
        </div>
      </Card>

      <Card>
        <h3 className="profile-section-title">Change Password</h3>
        <div className="profile-fields">
          <Input label="Current Password" type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} />
          <Input label="New Password" type="password" value={newPw} onChange={e => setNewPw(e.target.value)} />
          <Input label="Confirm New Password" type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} />
          <Button variant="primary" loading={changingPw} onClick={handleChangePassword}>Change Password</Button>
        </div>
      </Card>

      <Card>
        <h3 className="profile-section-title">Preferences</h3>
        <div className="profile-theme-toggle">
          <span>Theme</span>
          <button className="profile-theme-btn" onClick={toggleTheme}>
            {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
            {theme === 'dark' ? 'Dark' : 'Light'}
          </button>
        </div>
      </Card>

      <Card>
        <h3 className="profile-section-title" style={{ color: 'var(--danger)' }}>Danger Zone</h3>
        <Button variant="danger" leftIcon={LogOut} onClick={logout}>Logout</Button>
      </Card>
    </motion.div>
  );
}
