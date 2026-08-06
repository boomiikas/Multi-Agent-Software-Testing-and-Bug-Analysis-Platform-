import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { UserCog, Plus, Search, Trash2, Edit, ShieldCheck, User as UserIcon, AlertCircle } from 'lucide-react';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Modal from '../../components/Modal';
import EmptyState from '../../components/EmptyState';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { adminApi } from '../../services/api';
import './ManageUsers.css';

const emptyForm = { fullName: '', email: '', password: '', role: 'USER' };

export default function ManageUsers() {
  const { user: currentUser } = useAuth();
  const toast = useToast();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null); // null = create mode
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const { users } = await adminApi.listUsers();
      setUsers(users);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    if (!search) return users;
    const q = search.toLowerCase();
    return users.filter(u => u.fullName.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
  }, [users, search]);

  const openCreate = () => {
    setEditingUser(null);
    setForm(emptyForm);
    setFormError('');
    setModalOpen(true);
  };

  const openEdit = (u) => {
    setEditingUser(u);
    setForm({ fullName: u.fullName, email: u.email, password: '', role: u.role });
    setFormError('');
    setModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!form.fullName || form.fullName.trim().length < 2) return setFormError('Full name must be at least 2 characters.');
    if (!/\S+@\S+\.\S+/.test(form.email)) return setFormError('Enter a valid email.');
    if (!editingUser && form.password.length < 8) return setFormError('Password must be at least 8 characters.');

    setSaving(true);
    try {
      if (editingUser) {
        await adminApi.updateUser(editingUser.id, { fullName: form.fullName, email: form.email, role: form.role });
        toast.success('User updated.');
      } else {
        await adminApi.createUser(form);
        toast.success('User created.');
      }
      setModalOpen(false);
      loadUsers();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await adminApi.deleteUser(deleteTarget.id);
      toast.success('User deleted.');
      setDeleteTarget(null);
      loadUsers();
    } catch (err) {
      toast.error(err.message);
      setDeleteTarget(null);
    }
  };

  return (
    <motion.div className="manage-users" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-header__title"><UserCog size={24} /> Manage Users</h1>
          <p className="page-header__subtitle">{users.length} total accounts · Admin only</p>
        </div>
        <Button variant="primary" leftIcon={Plus} onClick={openCreate}>New User</Button>
      </div>

      <div className="mu-search">
        <Search size={16} className="mu-search__icon" />
        <input className="mu-search__input" placeholder="Search by name or email..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <Card padding="none">
        {loading ? (
          <div className="mu-loading">Loading users…</div>
        ) : filtered.length === 0 ? (
          <EmptyState title="No users found" description="Try a different search or create a new account." />
        ) : (
          <table className="mu-table">
            <thead>
              <tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th><th /></tr>
            </thead>
            <tbody>
              {filtered.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className="mu-name">
                      <div className="mu-avatar">{u.fullName.charAt(0)}</div>
                      {u.fullName}
                      {u.id === currentUser?.id && <Badge variant="default" size="sm">You</Badge>}
                    </div>
                  </td>
                  <td className="mu-email">{u.email}</td>
                  <td>
                    <Badge variant={u.role === 'ADMIN' ? 'primary' : 'default'} size="sm">
                      {u.role === 'ADMIN' ? <ShieldCheck size={12} /> : <UserIcon size={12} />} {u.role}
                    </Badge>
                  </td>
                  <td className="mu-date">{new Date(u.createdAt).toLocaleDateString()}</td>
                  <td>
                    <div className="mu-actions">
                      <button className="mu-icon-btn" onClick={() => openEdit(u)} aria-label="Edit"><Edit size={15} /></button>
                      <button
                        className="mu-icon-btn mu-icon-btn--danger"
                        onClick={() => setDeleteTarget(u)}
                        disabled={u.id === currentUser?.id}
                        title={u.id === currentUser?.id ? "You can't delete your own account" : 'Delete'}
                        aria-label="Delete"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingUser ? 'Edit User' : 'New User'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" loading={saving} onClick={handleSave}>{editingUser ? 'Save Changes' : 'Create User'}</Button>
          </>
        }
      >
        <form className="mu-form" onSubmit={handleSave}>
          {formError && <div className="auth-form__error"><AlertCircle size={16} /> {formError}</div>}
          <Input label="Full Name" value={form.fullName} onChange={e => setForm(f => ({ ...f, fullName: e.target.value }))} />
          <Input label="Email" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          {!editingUser && (
            <Input label="Password" type="password" placeholder="Min. 8 characters" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          )}
          <div className="mu-role-field">
            <label className="input__label">Role</label>
            <select className="pl-select" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} disabled={editingUser?.id === currentUser?.id}>
              <option value="USER">USER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete User"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete}>Delete</Button>
          </>
        }
      >
        <p>Are you sure you want to delete <strong>{deleteTarget?.fullName}</strong>? This can't be undone.</p>
      </Modal>
    </motion.div>
  );
}
