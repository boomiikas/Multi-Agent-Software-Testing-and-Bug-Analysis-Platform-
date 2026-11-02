import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bot, Clock, Cpu, MemoryStick, XCircle, RotateCcw, Search, Copy, Download, CheckCircle, Loader2, Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck, Terminal, Shield, CheckCircle2, AlertTriangle } from 'lucide-react';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Card from '../components/Card';
import { runSteps, mockLogs } from '../data/mockData';
import { testRunApi } from '../services/api';
import './RunMonitor.css';

const stepIcons = { Zap, FileText, GitBranch, Globe, ExternalLink, Play, Camera, Brain, FileCheck };

const defaultTestPlan = {
  strategy: 'Behavior-Driven Functional Automation & Exploratory Verification',
  scope: 'Authentication, Product Catalog, Cart Operations, and End-to-End Checkout Workflow',
  methodology: 'Playwright Headless Chromium + Declarative POM Assertions',
  riskAssessment: 'Low to Medium: Critical path checkout failure poses high revenue impact',
  acceptanceCriteria: 'Zero critical UI blockers, status 200 on all primary routes, complete checkout confirmation',
};

const defaultTestCases = [
  {
    id: 'TC-001',
    title: 'Verify Successful User Authentication with Valid Credentials',
    type: 'Smoke',
    priority: 'Critical',
    preconditions: 'Target website loaded, user credentials configured in SRS specification',
    steps: ['Navigate to https://www.saucedemo.com', 'Fill input#user-name with "standard_user"', 'Fill input#password with "secret_sauce"', 'Click input#login-button'],
    expected: 'Redirect to /inventory.html, .title element visible with text "Products"',
  },
  {
    id: 'TC-002',
    title: 'Verify Product Catalog Render and Add-to-Cart Action',
    type: 'Functional',
    priority: 'High',
    preconditions: 'User authenticated on /inventory.html',
    steps: ['Locate button#add-to-cart-sauce-labs-backpack', 'Click button', 'Verify span.shopping_cart_badge count'],
    expected: 'Cart badge displays "1", button text dynamically toggles to "Remove"',
  },
  {
    id: 'TC-003',
    title: 'Verify Shopping Cart Review and Navigation to Checkout',
    type: 'Functional',
    priority: 'High',
    preconditions: 'One product added to shopping cart',
    steps: ['Click a.shopping_cart_link', 'Verify URL is /cart.html', 'Click button#checkout'],
    expected: 'Redirect to /checkout-step-one.html, customer information form displayed',
  },
  {
    id: 'TC-004',
    title: 'Verify Customer Information Submission and Form Validation',
    type: 'Functional',
    priority: 'Critical',
    preconditions: 'User on checkout step one page',
    steps: ['Fill input#first-name with "Jane"', 'Fill input#last-name with "Doe"', 'Fill input#postal-code with "90210"', 'Click input#continue'],
    expected: 'Redirect to /checkout-step-two.html with complete pricing & tax summary',
  },
  {
    id: 'TC-005',
    title: 'Verify Order Finalization and Receipt Confirmation',
    type: 'End-to-End',
    priority: 'Critical',
    preconditions: 'Order overview verified on checkout step two',
    steps: ['Click button#finish', 'Verify URL is /checkout-complete.html', 'Verify h2.complete-header contains "Thank you for your order!"'],
    expected: 'Order confirmation banner displayed, cart badge cleared',
  },
  {
    id: 'TC-006',
    title: 'Verify Error Handling for Locked-Out or Invalid User',
    type: 'Security',
    priority: 'Medium',
    preconditions: 'User on login page',
    steps: ['Fill input#user-name with "locked_out_user"', 'Fill input#password with "secret_sauce"', 'Click input#login-button'],
    expected: 'Error message "Epic sadface: Sorry, this user has been locked out." is displayed',
  },
];

const defaultRcaDiagnoses = [
  {
    failureCategory: 'TEST_SCRIPT_ERROR',
    rootCauseHypothesis: 'Generated UI script selector discrepancy: DOM element selector was absent from SRS specification',
    supportingEvidence: ['Playwright selector validation: .title not declared in strict SRS document', 'Pipeline Stage 4 generator rejected ungrounded selector to prevent false positive'],
    artifactReferences: ['agent_4_ui_script.py', 'agent_1_requirements.txt'],
    confidence: 'HIGH',
    isHypothesis: false,
    retryEligible: false,
    retryReason: 'Deterministic selector mismatch will not resolve on retry without updated requirements or prompt tuning',
    recommendedAction: 'Update the SRS document to declare the required element selectors or constrain generator prompt',
  },
  {
    failureCategory: 'INFRASTRUCTURE_ISSUE',
    rootCauseHypothesis: 'Transient network latency spike caused socket timeout on external target',
    supportingEvidence: ['Socket read timeout after 10000ms reaching target CDN endpoint', 'Subsequent connectivity check succeeded with 120ms latency'],
    artifactReferences: ['agent_5_api_execution.json'],
    confidence: 'MEDIUM',
    isHypothesis: true,
    retryEligible: true,
    retryReason: 'Transient network delay is eligible for bounded backoff retry (Controlled Self-Healing)',
    recommendedAction: 'Retry controller executed with exponential backoff; target recovered without manual intervention',
  },
];

export default function RunMonitor() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const runId = searchParams.get('runId');
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'terminal');

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
        {/* Left: Terminal + Timeline / Test Planning / RCA */}
        <div className="rm-left">
          {/* Sub-Interface Tabs */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            <Button
              variant={activeTab === 'terminal' ? 'primary' : 'ghost'}
              size="sm"
              leftIcon={Terminal}
              onClick={() => setActiveTab('terminal')}
            >
              Live Terminal Logs
            </Button>
            <Button
              variant={activeTab === 'test-cases' ? 'primary' : 'ghost'}
              size="sm"
              leftIcon={FileText}
              onClick={() => setActiveTab('test-cases')}
            >
              Automated Test Planning & Test Cases
            </Button>
            <Button
              variant={activeTab === 'rca' ? 'primary' : 'ghost'}
              size="sm"
              leftIcon={Brain}
              onClick={() => setActiveTab('rca')}
            >
              Root Cause Analysis & Diagnostics
            </Button>
          </div>

          {activeTab === 'terminal' && (
            <Card padding="none" className="rm-terminal-card">
              <div className="rm-terminal__header">
                <span className="rm-terminal__title">Live Multi-Agent Execution Pipeline Output</span>
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
          )}

          {activeTab === 'test-cases' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Test Planning Strategy Card */}
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <GitBranch size={18} color="var(--primary)" />
                    <h3 style={{ fontWeight: 600, margin: 0, fontSize: 'var(--text-base)' }}>AI Test Planning & Execution Strategy</h3>
                  </div>
                  <Badge variant="primary" size="sm">Agent 2: TestPlanner-AI (Qwen2.5-7B)</Badge>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 12 }}>
                  <div style={{ padding: 10, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Strategy</div>
                    <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, marginTop: 2 }}>{defaultTestPlan.strategy}</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Execution Methodology</div>
                    <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, marginTop: 2 }}>{defaultTestPlan.methodology}</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Testing Scope</div>
                    <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, marginTop: 2 }}>{defaultTestPlan.scope}</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Risk Assessment</div>
                    <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, marginTop: 2 }}>{defaultTestPlan.riskAssessment}</div>
                  </div>
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  <strong>Acceptance Criteria:</strong> {defaultTestPlan.acceptanceCriteria}
                </div>
              </Card>

              {/* Generated Test Cases Matrix Card */}
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <FileText size={18} color="var(--success)" />
                    <h3 style={{ fontWeight: 600, margin: 0, fontSize: 'var(--text-base)' }}>Synthesized Test Cases Matrix ({defaultTestCases.length} Scenarios)</h3>
                  </div>
                  <Badge variant="success" size="sm">Agent 3: TestCaseGenerator-AI (DeepSeek-R1)</Badge>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {defaultTestCases.map((tc, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 12,
                        borderRadius: 6,
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border)',
                        borderLeft: tc.priority === 'Critical' ? '3px solid var(--danger)' : '3px solid var(--primary)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 'var(--text-xs)', color: 'var(--primary)' }}>
                            [{tc.id}]
                          </span>
                          <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>{tc.title}</span>
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Badge variant={tc.type === 'Smoke' ? 'primary' : tc.type === 'Security' ? 'warning' : 'default'} size="sm">
                            {tc.type}
                          </Badge>
                          <Badge variant={tc.priority === 'Critical' ? 'danger' : 'default'} size="sm">
                            {tc.priority}
                          </Badge>
                        </div>
                      </div>

                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginBottom: 6 }}>
                        <strong style={{ color: 'var(--text-muted)' }}>Preconditions:</strong> {tc.preconditions}
                      </div>

                      <div style={{ fontSize: 'var(--text-xs)', marginBottom: 6 }}>
                        <strong style={{ color: 'var(--text-muted)' }}>Action Steps:</strong>
                        <ol style={{ margin: '4px 0 0 0', paddingLeft: 18, color: 'var(--text-secondary)' }}>
                          {tc.steps.map((st, sIdx) => (
                            <li key={sIdx}>{st}</li>
                          ))}
                        </ol>
                      </div>

                      <div style={{ fontSize: 'var(--text-xs)', background: 'var(--bg-primary)', padding: '6px 10px', borderRadius: 4, color: 'var(--success)', fontWeight: 500 }}>
                        <CheckCircle2 size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                        <strong>Expected:</strong> {tc.expected}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'rca' && (
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Brain size={18} color="var(--warning)" />
                  <h3 style={{ fontWeight: 600, margin: 0, fontSize: 'var(--text-base)' }}>Root Cause Analysis & Controlled Self-Healing</h3>
                </div>
                <Badge variant="warning" size="sm">Agent 7: RootCauseAnalysis-AI</Badge>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {defaultRcaDiagnoses.map((diag, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: 14,
                      borderRadius: 8,
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border)',
                      borderLeft: diag.retryEligible ? '4px solid var(--success)' : '4px solid var(--danger)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: diag.retryEligible ? 'var(--warning)' : 'var(--danger)' }}>
                          [{diag.failureCategory}]
                        </span>
                        <span style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: 4,
                          background: diag.isHypothesis ? 'rgba(234, 179, 8, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                          color: diag.isHypothesis ? 'var(--warning)' : 'var(--success)',
                          fontWeight: 600,
                        }}>
                          {diag.isHypothesis ? 'Hypothesis' : 'Verified Fact'}
                        </span>
                      </div>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: diag.retryEligible ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: diag.retryEligible ? 'var(--success)' : 'var(--danger)',
                        fontWeight: 600,
                      }}>
                        {diag.retryEligible ? 'Retry Eligible' : 'Non-Retryable'}
                      </span>
                    </div>

                    <p style={{ margin: '6px 0', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {diag.rootCauseHypothesis}
                    </p>

                    <div style={{ margin: '8px 0', padding: 8, borderRadius: 4, background: 'var(--bg-primary)', fontSize: 'var(--text-xs)' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Supporting Evidence:</span>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: 18, color: 'var(--text-muted)' }}>
                        {diag.supportingEvidence.map((ev, eIdx) => (
                          <li key={eIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ marginTop: 8, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      <strong style={{ color: 'var(--primary)' }}>Self-Healing Controller Evaluation:</strong> {diag.retryReason}
                    </div>

                    <div style={{ marginTop: 4, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      <strong style={{ color: 'var(--success)' }}>Recommended Action:</strong> {diag.recommendedAction}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
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
