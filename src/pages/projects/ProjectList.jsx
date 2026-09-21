import { useState, useMemo, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Search, Grid, List, Play, Edit, Trash2, ExternalLink, Calendar, Filter, Loader2 } from 'lucide-react';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import ProgressBar from '../../components/ProgressBar';
import Modal from '../../components/Modal';
import EmptyState from '../../components/EmptyState';
import { projectApi } from '../../services/api';
import './ProjectList.css';

const statusMap = { completed: 'success', running: 'warning', failed: 'danger', pending: 'default' };

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [view, setView] = useState('grid');
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('newest');
  const [deleteId, setDeleteId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    projectApi.getProjects().then(data => {
      setProjects(data);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    let list = [...projects];
    if (search) list = list.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) || p.targetUrl.toLowerCase().includes(search.toLowerCase()));
    if (filter !== 'all') list = list.filter(p => p.status === filter);
    if (sort === 'newest') list.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    if (sort === 'oldest') list.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    if (sort === 'name-az') list.sort((a, b) => a.name.localeCompare(b.name));
    if (sort === 'name-za') list.sort((a, b) => b.name.localeCompare(a.name));
    return list;
  }, [projects, search, filter, sort]);

  const handleDelete = () => {
    projectApi.deleteProject(deleteId).then(() => {
      setProjects(prev => prev.filter(p => p.id !== deleteId));
      setDeleteId(null);
    });
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: 16 }}>
        <Loader2 className="animate-spin" size={32} color="var(--primary)" />
        <p style={{ color: 'var(--text-secondary)' }}>Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="project-list">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Projects</h1>
          <p className="page-header__subtitle">{projects.length} total projects</p>
        </div>
        <Link to="/projects/new"><Button variant="primary" leftIcon={Plus}>New Project</Button></Link>
      </div>

      <div className="pl-controls">
        <div className="pl-search">
          <Search size={16} className="pl-search__icon" />
          <input className="pl-search__input" placeholder="Search projects..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="pl-controls__right">
          <select className="pl-select" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
          <select className="pl-select" value={sort} onChange={e => setSort(e.target.value)}>
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name-az">Name A-Z</option>
            <option value="name-za">Name Z-A</option>
          </select>
          <div className="pl-view-toggle">
            <button className={`pl-view-btn ${view === 'grid' ? 'pl-view-btn--active' : ''}`} onClick={() => setView('grid')}><Grid size={16} /></button>
            <button className={`pl-view-btn ${view === 'list' ? 'pl-view-btn--active' : ''}`} onClick={() => setView('list')}><List size={16} /></button>
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No projects found" description="Try adjusting your search or create a new project." actionLabel="New Project" onAction={() => navigate('/projects/new')} />
      ) : view === 'grid' ? (
        <div className="grid grid--3">
          {filtered.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <Card className="pl-card" hoverable>
                <div className="pl-card__header">
                  <h3 className="pl-card__name">{p.name}</h3>
                  <Badge variant={statusMap[p.status]} dot pulse={p.status === 'running'} size="sm">{p.status}</Badge>
                </div>
                <a className="pl-card__url" href={p.targetUrl} target="_blank" rel="noreferrer"><ExternalLink size={12} /> {p.targetUrl}</a>
                <div className="pl-card__meta"><Calendar size={12} /> {new Date(p.createdAt).toLocaleDateString()}</div>
                {p.totalRuns > 0 && (
                  <div className="pl-card__progress">
                    <span className="pl-card__progress-label">Pass Rate: {p.passRate}%</span>
                    <ProgressBar value={p.passRate} variant={p.passRate > 80 ? 'success' : 'warning'} size="sm" />
                  </div>
                )}
                <div className="pl-card__actions">
                  <Button variant="primary" size="sm" leftIcon={Play} onClick={() => navigate('/run-monitor')}>Run</Button>
                  <Button variant="ghost" size="sm" leftIcon={Edit} onClick={() => navigate(`/projects/${p.id}`)}>Edit</Button>
                  <Button variant="danger-ghost" size="sm" leftIcon={Trash2} onClick={() => setDeleteId(p.id)}>Delete</Button>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <Card padding="none">
          <table className="dash-table" style={{ width: '100%' }}>
            <thead><tr><th>Name</th><th>URL</th><th>Status</th><th>Pass Rate</th><th>Runs</th><th>Actions</th></tr></thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 500 }}>{p.name}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>{p.targetUrl}</td>
                  <td><Badge variant={statusMap[p.status]} size="sm">{p.status}</Badge></td>
                  <td>{p.passRate}%</td>
                  <td>{p.totalRuns}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <Button variant="ghost" size="sm" leftIcon={Play} onClick={() => navigate('/run-monitor')} />
                      <Button variant="ghost" size="sm" leftIcon={Edit} onClick={() => navigate(`/projects/${p.id}`)} />
                      <Button variant="danger-ghost" size="sm" leftIcon={Trash2} onClick={() => setDeleteId(p.id)} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Modal isOpen={!!deleteId} onClose={() => setDeleteId(null)} title="Delete Project" size="sm" footer={
        <><Button variant="ghost" onClick={() => setDeleteId(null)}>Cancel</Button><Button variant="danger" onClick={handleDelete}>Delete</Button></>
      }>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>Are you sure you want to delete this project? This action cannot be undone.</p>
      </Modal>
    </div>
  );
}
