import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Bot, Clock, Cpu, MemoryStick, XCircle, RotateCcw, Search, Copy, Download, CheckCircle, Loader2, Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck } from 'lucide-react';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Card from '../components/Card';
import { runSteps, mockLogs } from '../data/mockData';
import './RunMonitor.css';

const stepIcons = { Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck };

export default function RunMonitor() {
  const [currentStep, setCurrentStep] = useState(0);
  const [logs, setLogs] = useState([]);
  const [logIndex, setLogIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [cpu, setCpu] = useState(35);
  const [memory, setMemory] = useState(42);
  const [searchQuery, setSearchQuery] = useState('');
  const logsEndRef = useRef(null);

  // Advance steps
  useEffect(() => {
    if (currentStep >= 9) return;
    const t = setInterval(() => setCurrentStep(p => Math.min(p + 1, 9)), 3000);
    return () => clearInterval(t);
  }, [currentStep]);

  // Stream logs
  useEffect(() => {
    if (logIndex >= mockLogs.length) return;
    const t = setInterval(() => {
      setLogIndex(p => {
        if (p < mockLogs.length) {
          setLogs(prev => [...prev, mockLogs[p]]);
          return p + 1;
        }
        return p;
      });
    }, 180);
    return () => clearInterval(t);
  }, [logIndex]);

  // Auto-scroll logs
  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  // Elapsed timer
  useEffect(() => {
    const t = setInterval(() => setElapsed(p => p + 1), 1000);
    return () => clearInterval(t);
  }, []);

  // Simulate metrics
  useEffect(() => {
    const t = setInterval(() => {
      setCpu(30 + Math.random() * 35);
      setMemory(40 + Math.random() * 30);
    }, 2000);
    return () => clearInterval(t);
  }, []);

  const progress = Math.round((currentStep / 9) * 100);
  const isComplete = currentStep >= 9;
  const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  const filteredLogs = searchQuery ? logs.filter(l => l.message.toLowerCase().includes(searchQuery.toLowerCase())) : logs;

  return (
    <div className="run-monitor">
      {/* Header */}
      <div className="rm-header">
        <div className="rm-header__left">
          <h1 className="rm-header__title">E-Commerce Checkout Flow</h1>
          <div className="rm-header__meta">
            <Badge variant={isComplete ? 'success' : 'warning'} dot pulse={!isComplete}>{isComplete ? 'Completed' : 'Running'}</Badge>
            <span className="rm-header__agent"><Bot size={14} /> TestMaster-v3</span>
            <span className="rm-header__time"><Clock size={14} /> {formatTime(elapsed)}</span>
          </div>
        </div>
        <div className="rm-header__actions">
          <Button variant="ghost" leftIcon={RotateCcw} size="sm">Restart</Button>
          <Button variant="danger" leftIcon={XCircle} size="sm">Cancel</Button>
        </div>
      </div>

      {/* Step Progress */}
      <Card className="rm-steps-card" padding="lg">
        <div className="rm-steps">
          {runSteps.map((step, i) => {
            const Icon = stepIcons[step.icon] || Zap;
            const state = i < currentStep ? 'done' : i === currentStep ? 'active' : 'upcoming';
            return (
              <div key={step.id} className="rm-step-wrapper">
                <div className={`rm-step rm-step--${state}`}>
                  <div className="rm-step__circle">
                    {state === 'done' ? <CheckCircle size={18} /> : state === 'active' ? <Loader2 size={18} className="animate-spin" /> : <Icon size={16} />}
                  </div>
                  <span className="rm-step__name">{step.name}</span>
                </div>
                {i < 8 && <div className={`rm-step__line rm-step__line--${i < currentStep ? 'done' : 'upcoming'}`} />}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Main Content */}
      <div className="rm-content">
        {/* Left: Terminal + Timeline */}
        <div className="rm-left">
          <Card padding="none" className="rm-terminal-card">
            <div className="rm-terminal__header">
              <span className="rm-terminal__title">Terminal Output</span>
              <div className="rm-terminal__actions">
                <div className="rm-terminal__search">
                  <Search size={14} />
                  <input placeholder="Search logs..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                </div>
                <button className="rm-terminal__btn" title="Copy" onClick={() => navigator.clipboard.writeText(logs.map(l => `${l.time} [${l.level}] ${l.message}`).join('\n'))}><Copy size={14} /></button>
                <button className="rm-terminal__btn" title="Download"><Download size={14} /></button>
              </div>
            </div>
            <div className="rm-terminal__body">
              {filteredLogs.map((log, i) => (
                <div key={i} className="rm-log-line">
                  <span className="rm-log__num">{i + 1}</span>
                  <span className="rm-log__time">{log.time}</span>
                  <span className={`rm-log__level rm-log__level--${log.level}`}>[{log.level.toUpperCase()}]</span>
                  <span className="rm-log__msg">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
              {!isComplete && <div className="rm-log-line rm-log-cursor"><span className="rm-cursor">█</span></div>}
            </div>
          </Card>
        </div>

        {/* Right: Progress + Metrics */}
        <div className="rm-right">
          <Card className="rm-progress-card">
            <div className="rm-circle-progress">
              <svg viewBox="0 0 120 120" className="rm-circle-svg">
                <circle cx="60" cy="60" r="52" className="rm-circle-bg" />
                <motion.circle cx="60" cy="60" r="52" className="rm-circle-fill"
                  strokeDasharray={327} initial={{ strokeDashoffset: 327 }}
                  animate={{ strokeDashoffset: 327 - (327 * progress) / 100 }}
                  transition={{ duration: 0.5 }}
                />
              </svg>
              <div className="rm-circle-text">
                <span className="rm-circle-percent">{progress}%</span>
                <span className="rm-circle-label">Complete</span>
              </div>
            </div>
            <p className="rm-estimated">Est. remaining: {isComplete ? 'Done' : `${Math.max(0, Math.round((9 - currentStep) * 0.5))}m ${Math.round(Math.random() * 30)}s`}</p>
          </Card>

          <Card className="rm-metrics">
            <h4 className="rm-metrics__title">System Metrics</h4>
            <div className="rm-metric">
              <div className="rm-metric__header"><Cpu size={14} /> <span>CPU Usage</span><span className="rm-metric__value">{cpu.toFixed(0)}%</span></div>
              <div className="rm-metric__bar"><motion.div className="rm-metric__fill rm-metric__fill--cpu" animate={{ width: `${cpu}%` }} /></div>
            </div>
            <div className="rm-metric">
              <div className="rm-metric__header"><MemoryStick size={14} /> <span>Memory</span><span className="rm-metric__value">{memory.toFixed(0)}%</span></div>
              <div className="rm-metric__bar"><motion.div className="rm-metric__fill rm-metric__fill--mem" animate={{ width: `${memory}%` }} /></div>
            </div>
          </Card>

          <Card className="rm-agent-card">
            <div className="rm-agent__header"><Bot size={20} className="rm-agent__bot" /> <span>TestMaster-v3</span></div>
            <p className="rm-agent__action">{currentStep < 9 ? runSteps[currentStep]?.description : 'All steps completed'}</p>
            <div className="rm-agent__timer"><Clock size={14} /> Running for {formatTime(elapsed)}</div>
          </Card>
        </div>
      </div>
    </div>
  );
}
