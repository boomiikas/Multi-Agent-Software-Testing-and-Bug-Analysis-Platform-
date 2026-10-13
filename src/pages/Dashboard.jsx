import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FolderKanban, Activity, TrendingUp, Clock, Plus, Play, FileText, Code2, ArrowUpRight, ArrowDownRight, ExternalLink, Bot, Loader2 } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import ProgressBar from '../components/ProgressBar';
import { dashboardApi, projectApi } from '../services/api';
import './Dashboard.css';

const quickActions = [
  { title: 'New Project', desc: 'Create a new testing project', icon: Plus, to: '/projects/new', color: 'var(--primary)' },
  { title: 'Start Run', desc: 'Execute a test run', icon: Play, to: '/run-monitor', color: 'var(--success)' },
  { title: 'View Reports', desc: 'Browse test reports', icon: FileText, to: '/success', color: 'var(--warning)' },
  { title: 'API Docs', desc: 'Developer documentation', icon: Code2, to: '/db-models', color: 'var(--info)' },
];

const statusMap = { completed: 'success', running: 'warning', failed: 'danger', pending: 'default' };

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatDuration(s) {
  if (!s) return '—';
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec}s`;
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    Promise.all([
      dashboardApi.getStats(),
      dashboardApi.getRecentRuns(),
      projectApi.getProjects()
    ]).then(([s, r, p]) => {
      setStats(s);
      setRuns(r);
      setProjects(p);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: 16 }}>
        <Loader2 className="animate-spin" size={32} color="var(--primary)" />
        <p style={{ color: 'var(--text-secondary)' }}>Loading dashboard...</p>
      </div>
    );
  }

  const statCards = [
    { label: 'Total Projects', value: stats.totalProjects, trend: stats.totalProjectsTrend, icon: FolderKanban, color: 'var(--primary)' },
    { label: 'Active Runs', value: stats.activeRuns, trend: stats.activeRunsTrend, icon: Activity, color: 'var(--warning)' },
    { label: 'Pass Rate', value: `${stats.passRate}%`, trend: stats.passRateTrend, icon: TrendingUp, color: 'var(--success)' },
    { label: 'Avg Duration', value: stats.avgDuration, trend: stats.avgDurationTrend, icon: Clock, color: 'var(--info)' },
  ];

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Dashboard</h1>
          <p className="page-header__subtitle">Overview of your testing platform</p>
        </div>
        <Link to="/projects/new">
          <motion.button className="btn btn--primary btn--md" whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
            <Plus size={16} /> New Project
          </motion.button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid--4 stagger">
        {statCards.map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <Card className="dash-stat" glowing>
              <div className="dash-stat__icon" style={{ background: `${s.color}15`, color: s.color }}>
                <s.icon size={22} />
              </div>
              <div className="dash-stat__info">
                <span className="dash-stat__label">{s.label}</span>
                <span className="dash-stat__value">{s.value}</span>
              </div>
              <span className={`dash-stat__trend ${s.trend >= 0 ? 'dash-stat__trend--up' : 'dash-stat__trend--down'}`}>
                {s.trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {Math.abs(s.trend)}%
              </span>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <h3 className="dashboard__section-title">Quick Actions</h3>
      <div className="grid grid--4">
        {quickActions.map((a, i) => (
          <Link key={i} to={a.to} style={{ textDecoration: 'none' }}>
            <Card clickable className="dash-action">
              <div className="dash-action__icon" style={{ background: `${a.color}15`, color: a.color }}>
                <a.icon size={22} />
              </div>
              <h4 className="dash-action__title">{a.title}</h4>
              <p className="dash-action__desc">{a.desc}</p>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent Runs */}
      <h3 className="dashboard__section-title">Recent Runs</h3>
      <Card padding="none" className="dash-table-card">
        <div className="dash-table-wrapper">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Project</th><th>Status</th><th>Agent</th><th>Duration</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr><td colSpan="5" style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>No recent runs</td></tr>
              ) : runs.map(run => (
                <tr key={run.id}>
                  <td className="dash-table__project">{run.projectName}</td>
                  <td><Badge variant={statusMap[run.status]} dot pulse={run.status === 'running'}>{run.status}</Badge></td>
                  <td><span className="dash-table__agent"><Bot size={14} /> {run.agent}</span></td>
                  <td>{formatDuration(run.duration)}</td>
                  <td className="dash-table__date">{formatDate(run.startTime)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Projects */}
      <div className="dashboard__projects-header">
        <h3 className="dashboard__section-title">Recent Projects</h3>
        <Link to="/projects" className="dashboard__view-all">View All <ExternalLink size={14} /></Link>
      </div>
      <div className="grid grid--3">
        {projects.length === 0 ? (
           <div style={{ padding: 24, color: 'var(--text-muted)', gridColumn: 'span 3' }}>No projects yet.</div>
        ) : projects.slice(0, 3).map((p, i) => (
          <motion.div key={p.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i }}>
            <Card clickable className="dash-project">
              <div className="dash-project__header">
                <h4 className="dash-project__name">{p.name}</h4>
                <Badge variant={statusMap[p.status]} size="sm">{p.status}</Badge>
              </div>
              <p className="dash-project__url">{p.targetUrl}</p>
              {p.totalRuns > 0 && (
                <div className="dash-project__stats">
                  <span className="dash-project__stat-label">Pass Rate</span>
                  <ProgressBar value={p.passRate} variant={p.passRate > 80 ? 'success' : p.passRate > 50 ? 'warning' : 'danger'} size="sm" showLabel />
                </div>
              )}
              <div className="dash-project__footer">
                <span>{p.totalRuns} runs</span>
                <span>{formatDate(p.lastRunAt)}</span>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
