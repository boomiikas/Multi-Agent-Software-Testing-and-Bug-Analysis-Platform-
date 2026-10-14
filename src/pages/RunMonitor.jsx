import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bot, Clock, Cpu, MemoryStick, XCircle, RotateCcw, Search, Copy, Download, CheckCircle, Loader2, Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck } from 'lucide-react';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Card from '../components/Card';
import { runSteps, mockLogs } from '../data/mockData';
import { testRunApi } from '../services/api';
import './RunMonitor.css';

const stepIcons = { Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck };

export default function RunMonitor() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const runId = searchParams.get('runId');

  const [runData, setRunData] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [logs, setLogs] = useState([]);
  const [elapsed, setElapsed] = useState(0);
  const [cpu, setCpu] = useState(35);
  const [memory, setMemory] = useState(42);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const logsEndRef = useRef(null);

  // Poll live run status when runId is present
  useEffect(() => {
    if (!runId) return;

    let isMounted = true;
    const fetchStatus = async () => {
      try {
        const data = await testRunApi.getRunStatus(runId);
        if (!isMounted) return;
        setRunData(data);
        setCurrentStep(data.stepsCompleted || 0);
        if (Array.isArray(data.logs) && data.logs.length > 0) {
          setLogs(data.logs);
        }
        if (data.duration) {
          setElapsed(data.duration);
        }

        // Automatic redirect upon completion
        if (data.status === 'completed') {
          setTimeout(() => {
            if (isMounted) navigate(`/success?runId=${runId}`);
          }, 2000);
        } else if (data.status === 'failed' || data.status === 'cancelled') {
          setTimeout(() => {
            if (isMounted) navigate(`/failure?runId=${runId}`);
          }, 2500);
        }
      } catch (err) {
        console.error('Error polling run status:', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 1800);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [runId, navigate]);

  // Fallback demo advancement when no runId is present
  useEffect(() => {
    if (runId) return;
    if (currentStep >= 9) return;
    const t = setInterval(() => setCurrentStep(p => Math.min(p + 1, 9)), 3000);
    return () => clearInterval(t);
  }, [runId, currentStep]);

  // Fallback demo log streaming when no runId is present
  useEffect(() => {
    if (runId) return;
    let idx = 0;
    const t = setInterval(() => {
      if (idx < mockLogs.length) {
        setLogs(prev => [...prev, mockLogs[idx]]);
        idx += 1;
      }
    }, 250);
    return () => clearInterval(t);
  }, [runId]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Elapsed timer (increment while running)
  useEffect(() => {
    if (runData && (runData.status === 'completed' || runData.status === 'failed' || runData.status === 'cancelled')) {
      return;
    }
    const t = setInterval(() => setElapsed(p => p + 1), 1000);
    return () => clearInterval(t);
  }, [runData]);

  // Simulated metrics
  useEffect(() => {
    const t = setInterval(() => {
      setCpu(30 + Math.random() * 35);
      setMemory(40 + Math.random() * 30);
    }, 2000);
    return () => clearInterval(t);
  }, []);

  const handleCancel = async () => {
    if (!runId) return;
    try {
      setActionLoading(true);
      await testRunApi.cancelRun(runId);
      navigate(`/failure?runId=${runId}`);
    } catch (err) {
      alert(err.message || 'Failed to cancel run');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestart = async () => {
    if (!runId) return;
    try {
      setActionLoading(true);
      const newRun = await testRunApi.restartRun(runId);
      navigate(`/run-monitor?runId=${newRun.id || newRun.runId}`);
    } catch (err) {
      alert(err.message || 'Failed to restart run');
    } finally {
      setActionLoading(false);
    }
  };

  const progress = Math.min(100, Math.round((currentStep / 9) * 100));
  const statusStr = runData?.status || (currentStep >= 9 ? 'completed' : 'running');
  const isComplete = statusStr === 'completed';
  const isFailed = statusStr === 'failed' || statusStr === 'cancelled';
  const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  const filteredLogs = searchQuery
    ? logs.filter(l => (l.message || '').toLowerCase().includes(searchQuery.toLowerCase()))
    : logs;

  const projectTitle = runData?.projectName || 'Multi-Agent Test Pipeline';

  return (
    <div className="run-monitor">
      {/* Header */}
      <div className="rm-header">
        <div className="rm-header__left">
          <h1 className="rm-header__title">{projectTitle}</h1>
          <div className="rm-header__meta">
            <Badge
              variant={isComplete ? 'success' : isFailed ? 'danger' : 'warning'}
              dot
              pulse={!isComplete && !isFailed}
            >
              {statusStr.toUpperCase()}
            </Badge>
            <span className="rm-header__agent"><Bot size={14} /> {runData?.agent || 'TestMaster-v3'}</span>
            <span className="rm-header__time"><Clock size={14} /> {formatTime(elapsed)}</span>
            {runData?.currentStage && (
              <span className="rm-header__agent" style={{ color: 'var(--primary)' }}>
                Stage: {runData.currentStage}
              </span>
            )}
          </div>
        </div>
        <div className="rm-header__actions">
          {runId && (
            <>
              <Button
                variant="ghost"
                leftIcon={RotateCcw}
                size="sm"
                loading={actionLoading}
                onClick={handleRestart}
              >
                Restart
              </Button>
              <Button
                variant="danger"
                leftIcon={XCircle}
                size="sm"
                disabled={isComplete || isFailed}
                loading={actionLoading}
                onClick={handleCancel}
              >
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Step Progress */}
      <Card className="rm-steps-card" padding="lg">
        <div className="rm-steps">
          {runSteps.map((step, i) => {
            const Icon = stepIcons[step.icon] || Zap;
            const state = i < currentStep ? 'done' : i === currentStep && !isComplete && !isFailed ? 'active' : isComplete ? 'done' : 'upcoming';
            return (
              <div key={step.id} className="rm-step-wrapper">
                <div className={`rm-step rm-step--${state}`}>
                  <div className="rm-step__circle">
                    {state === 'done' ? (
                      <CheckCircle size={18} />
                    ) : state === 'active' ? (
                      <Loader2 size={18} className="animate-spin" />
                    ) : (
                      <Icon size={16} />
                    )}
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
              <span className="rm-terminal__title">Live Pipeline Output</span>
              <div className="rm-terminal__actions">
                <div className="rm-terminal__search">
                  <Search size={14} />
                  <input
                    placeholder="Search logs..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                  />
                </div>
                <button
                  className="rm-terminal__btn"
                  title="Copy"
                  onClick={() =>
                    navigator.clipboard.writeText(
                      logs.map(l => `${l.time || ''} [${(l.level || 'info').toUpperCase()}] ${l.message || ''}`).join('\n')
                    )
                  }
                >
                  <Copy size={14} />
                </button>
                <button
                  className="rm-terminal__btn"
                  title="Download"
                  onClick={() => {
                    const blob = new Blob(
                      [logs.map(l => `${l.time || ''} [${(l.level || 'info').toUpperCase()}] ${l.message || ''}`).join('\n')],
                      { type: 'text/plain' }
                    );
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = `pipeline-run-${runId || 'logs'}.txt`;
                    a.click();
                  }}
                >
                  <Download size={14} />
                </button>
              </div>
            </div>
            <div className="rm-terminal__body">
              {filteredLogs.map((log, i) => (
                <div key={i} className="rm-log-line">
                  <span className="rm-log__num">{i + 1}</span>
                  <span className="rm-log__time">{log.time || log.timestamp?.slice(11, 19) || ''}</span>
                  <span className={`rm-log__level rm-log__level--${(log.level || 'info').toLowerCase()}`}>
                    [{(log.level || 'info').toUpperCase()}]
                  </span>
                  <span className="rm-log__msg">{log.message || ''}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
              {!isComplete && !isFailed && (
                <div className="rm-log-line rm-log-cursor">
                  <span className="rm-cursor">█</span>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right: Progress + Metrics */}
        <div className="rm-right">
          <Card className="rm-progress-card">
            <div className="rm-circle-progress">
              <svg viewBox="0 0 120 120" className="rm-circle-svg">
                <circle cx="60" cy="60" r="52" className="rm-circle-bg" />
                <motion.circle
                  cx="60"
                  cy="60"
                  r="52"
                  className="rm-circle-fill"
                  strokeDasharray={327}
                  initial={{ strokeDashoffset: 327 }}
                  animate={{ strokeDashoffset: 327 - (327 * progress) / 100 }}
                  transition={{ duration: 0.5 }}
                />
              </svg>
              <div className="rm-circle-text">
                <span className="rm-circle-percent">{progress}%</span>
                <span className="rm-circle-label">{isComplete ? 'Done' : 'Complete'}</span>
              </div>
            </div>
            <p className="rm-estimated">
              {isComplete
                ? 'Execution Finished'
                : isFailed
                ? 'Execution Terminated'
                : `Step ${currentStep} of 9 completed`}
            </p>
          </Card>

          <Card className="rm-metrics">
            <h4 className="rm-metrics__title">System Metrics</h4>
            <div className="rm-metric">
              <div className="rm-metric__header">
                <Cpu size={14} /> <span>CPU Usage</span>
                <span className="rm-metric__value">{cpu.toFixed(0)}%</span>
              </div>
              <div className="rm-metric__bar">
                <motion.div className="rm-metric__fill rm-metric__fill--cpu" animate={{ width: `${cpu}%` }} />
              </div>
            </div>
            <div className="rm-metric">
              <div className="rm-metric__header">
                <MemoryStick size={14} /> <span>Memory</span>
                <span className="rm-metric__value">{memory.toFixed(0)}%</span>
              </div>
              <div className="rm-metric__bar">
                <motion.div className="rm-metric__fill rm-metric__fill--mem" animate={{ width: `${memory}%` }} />
              </div>
            </div>
          </Card>

          <Card className="rm-agent-card">
            <div className="rm-agent__header">
              <Bot size={20} className="rm-agent__bot" />
              <span>{runData?.agent || 'TestMaster-v3'}</span>
            </div>
            <p className="rm-agent__action">
              {currentStep < 9
                ? runSteps[currentStep]?.description || 'Multi-agent orchestration in progress'
                : 'All stages finished successfully.'}
            </p>
            <div className="rm-agent__timer">
              <Clock size={14} /> Running for {formatTime(elapsed)}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
