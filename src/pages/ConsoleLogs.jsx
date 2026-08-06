import { useState, useEffect, useRef } from 'react';
import { Search, Copy, Download, ArrowDown } from 'lucide-react';
import { mockLogs } from '../data/mockData';
import Button from '../components/Button';
import './ConsoleLogs.css';

export default function ConsoleLogs() {
  const [logs, setLogs] = useState([]);
  const [logIdx, setLogIdx] = useState(0);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const endRef = useRef(null);

  useEffect(() => {
    if (logIdx >= mockLogs.length) return;
    const t = setInterval(() => {
      setLogIdx(p => { if (p < mockLogs.length) { setLogs(prev => [...prev, mockLogs[p]]); return p + 1; } return p; });
    }, 120);
    return () => clearInterval(t);
  }, [logIdx]);

  useEffect(() => { if (autoScroll) endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs, autoScroll]);

  const filtered = logs.filter(l => {
    if (filter !== 'all' && l.level !== filter) return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const handleCopy = () => navigator.clipboard.writeText(filtered.map(l => `[${l.time}] [${l.level.toUpperCase()}] ${l.message}`).join('\n'));
  const handleDownload = () => {
    const blob = new Blob([filtered.map(l => `[${l.time}] [${l.level.toUpperCase()}] ${l.message}`).join('\n')], { type: 'text/plain' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'agent-logs.txt'; a.click();
  };

  return (
    <div className="console-page">
      <div className="page-header">
        <div><h1 className="page-header__title">Console Logs</h1><p className="page-header__subtitle">{logs.length} log entries</p></div>
      </div>
      <div className="console-controls">
        <div className="console-search"><Search size={14} /><input placeholder="Search logs..." value={search} onChange={e => setSearch(e.target.value)} /></div>
        <select className="pl-select" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="all">All Levels</option><option value="info">Info</option><option value="success">Success</option><option value="warning">Warning</option><option value="error">Error</option>
        </select>
        <button className={`console-scroll-btn ${autoScroll ? 'console-scroll-btn--active' : ''}`} onClick={() => setAutoScroll(!autoScroll)}><ArrowDown size={14} /> Auto-scroll</button>
        <Button variant="ghost" size="sm" leftIcon={Copy} onClick={handleCopy}>Copy</Button>
        <Button variant="ghost" size="sm" leftIcon={Download} onClick={handleDownload}>Download</Button>
      </div>
      <div className="console-terminal">
        {filtered.map((log, i) => (
          <div key={i} className="console-line" onClick={() => navigator.clipboard.writeText(log.message)} title="Click to copy">
            <span className="console-line__num">{i + 1}</span>
            <span className="console-line__time">[{log.time}]</span>
            <span className={`console-line__level console-line__level--${log.level}`}>[{log.level.toUpperCase()}]</span>
            <span className="console-line__msg">{search ? log.message.split(new RegExp(`(${search})`, 'gi')).map((part, j) => part.toLowerCase() === search.toLowerCase() ? <mark key={j} className="console-highlight">{part}</mark> : part) : log.message}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
