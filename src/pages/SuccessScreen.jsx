import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, Download, Share2, Copy, Terminal, Play, Clock, Bot, BarChart3, FlaskConical } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import MarkdownViewer from '../components/MarkdownViewer';
import { mockReport } from '../data/mockData';
import './SuccessScreen.css';

export default function SuccessScreen() {
  const [confetti, setConfetti] = useState([]);

  useEffect(() => {
    const colors = ['#4F8CFF', '#22C55E', '#F59E0B', '#EF4444', '#38BDF8', '#A78BFA'];
    const pieces = Array.from({ length: 40 }, (_, i) => ({
      id: i, left: Math.random() * 100, delay: Math.random() * 2, duration: 2 + Math.random() * 3,
      color: colors[Math.floor(Math.random() * colors.length)], size: 4 + Math.random() * 8,
    }));
    setConfetti(pieces);
  }, []);

  const stats = [
    { label: 'Tests Passed', value: '11/12', icon: CheckCircle, color: 'var(--success)' },
    { label: 'Pass Rate', value: '91.67%', icon: BarChart3, color: 'var(--primary)' },
    { label: 'Duration', value: '12m 00s', icon: Clock, color: 'var(--warning)' },
    { label: 'Agent', value: 'TestMaster-v3', icon: Bot, color: 'var(--info)' },
  ];

  const handleCopy = () => navigator.clipboard.writeText(mockReport);
  const handleDownload = () => {
    const blob = new Blob([mockReport], { type: 'text/markdown' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'test-report.md'; a.click();
  };

  return (
    <div className="success-page">
      <div className="success-confetti">
        {confetti.map(c => (
          <div key={c.id} className="confetti-piece" style={{ left: `${c.left}%`, animationDelay: `${c.delay}s`, animationDuration: `${c.duration}s`, backgroundColor: c.color, width: c.size, height: c.size }} />
        ))}
      </div>

      <motion.div className="success-header" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ type: 'spring', duration: 0.6 }}>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.3 }}>
          <CheckCircle size={72} color="var(--success)" strokeWidth={1.5} />
        </motion.div>
        <h1 className="success-header__title">Test Run Completed Successfully!</h1>
        <p className="success-header__subtitle">E-Commerce Checkout Flow</p>
      </motion.div>

      <div className="grid grid--4" style={{ marginBottom: 32 }}>
        {stats.map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 + i * 0.1 }}>
            <Card className="success-stat" glowing>
              <s.icon size={24} color={s.color} />
              <span className="success-stat__value">{s.value}</span>
              <span className="success-stat__label">{s.label}</span>
            </Card>
          </motion.div>
        ))}
      </div>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontWeight: 600 }}>Test Report</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button variant="primary" size="sm" leftIcon={Download} onClick={handleDownload}>Download</Button>
            <Button variant="secondary" size="sm" leftIcon={Share2}>Share</Button>
            <Button variant="ghost" size="sm" leftIcon={Copy} onClick={handleCopy}>Copy</Button>
          </div>
        </div>
        <MarkdownViewer content={mockReport} />
      </Card>

      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <Link to="/console"><Button variant="ghost" leftIcon={Terminal}>View Logs</Button></Link>
        <Link to="/run-monitor"><Button variant="ghost" leftIcon={Play}>New Run</Button></Link>
      </div>
    </div>
  );
}
