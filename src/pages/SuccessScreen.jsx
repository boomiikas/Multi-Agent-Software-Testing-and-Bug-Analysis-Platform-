import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Shield,
  Server,
  Download,
  Share2,
  Copy,
  Terminal,
  Play,
  Clock,
  Bot,
  BarChart3,
  FileCode,
  Paperclip,
  Check,
  Globe,
} from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import MarkdownViewer from '../components/MarkdownViewer';
import { mockReport } from '../data/mockData';
import { testRunApi } from '../services/api';
import './SuccessScreen.css';

const severityVariant = {
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'default',
  INFO: 'default',
};

export default function SuccessScreen() {
  const [searchParams] = useSearchParams();
  const runId = searchParams.get('runId');

  const [confetti, setConfetti] = useState([]);
  const [reportText, setReportText] = useState(mockReport);
  const [runData, setRunData] = useState(null);
  const [loading, setLoading] = useState(!!runId);

  useEffect(() => {
    const colors = ['#4F8CFF', '#22C55E', '#F59E0B', '#EF4444', '#38BDF8', '#A78BFA'];
    const pieces = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 2,
      duration: 2 + Math.random() * 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 4 + Math.random() * 8,
    }));
    setConfetti(pieces);
  }, []);

  useEffect(() => {
    if (!runId) return;

    let isMounted = true;
    Promise.all([
      testRunApi.getRunStatus(runId).catch(() => null),
      testRunApi.getReport(runId).catch(() => null),
    ]).then(([statusData, reportData]) => {
      if (!isMounted) return;
      if (statusData) setRunData(statusData);
      if (reportData?.report) {
        setReportText(reportData.report);
      } else if (statusData?.report) {
        setReportText(statusData.report);
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [runId]);

  const durationSec = runData?.duration || 720;
  const formatDuration = (s) => `${Math.floor(s / 60)}m ${(s % 60).toString().padStart(2, '0')}s`;

  const testsTotal = runData?.metrics?.testsTotal || 10;
  const testsPassed = runData?.metrics?.testsPassed || 10;
  const passRate = runData?.metrics?.passRate || 100;

  const stats = [
    { label: 'Tests Passed', value: `${testsPassed}/${testsTotal}`, icon: CheckCircle, color: 'var(--success)' },
    { label: 'Pass Rate', value: `${passRate}%`, icon: BarChart3, color: 'var(--primary)' },
    { label: 'Duration', value: formatDuration(durationSec), icon: Clock, color: 'var(--warning)' },
    { label: 'Agent', value: runData?.agent || 'TestMaster-v3', icon: Bot, color: 'var(--info)' },
  ];

  const handleCopy = () => navigator.clipboard.writeText(reportText);
  const handleDownload = () => {
    const blob = new Blob([reportText], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `test-report-${runId || 'latest'}.md`;
    a.click();
  };

  const projectTitle = runData?.projectName || 'Multi-Agent Test Pipeline';

  const apiExec = runData?.apiExecution || runData?.findings?.apiExecution;
  const secExec = runData?.securityExecution || runData?.findings?.securityExecution;

  return (
    <div className="success-page">
      <div className="success-confetti">
        {confetti.map(c => (
          <div
            key={c.id}
            className="confetti-piece"
            style={{
              left: `${c.left}%`,
              animationDelay: `${c.delay}s`,
              animationDuration: `${c.duration}s`,
              backgroundColor: c.color,
              width: c.size,
              height: c.size,
            }}
          />
        ))}
      </div>

      <motion.div
        className="success-header"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', duration: 0.6 }}
      >
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.3 }}>
          <CheckCircle size={72} color="var(--success)" strokeWidth={1.5} />
        </motion.div>
        <h1 className="success-header__title">Test Run Completed Successfully!</h1>
        <p className="success-header__subtitle">{projectTitle}</p>
      </motion.div>

      <div className="grid grid--4" style={{ marginBottom: 32 }}>
        {stats.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
          >
            <Card className="success-stat" glowing>
              <s.icon size={24} color={s.color} />
              <span className="success-stat__value">{s.value}</span>
              <span className="success-stat__label">{s.label}</span>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Execution Architecture Breakdown */}
      {runData?.limitations && runData.limitations.length > 0 && (
        <Card style={{ marginBottom: 24, borderLeft: '4px solid var(--info)' }}>
          <h4 style={{ fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={18} /> Execution Architecture & Tool Integration Breakdown
          </h4>
          <ul style={{ paddingLeft: 20, margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
            {runData.limitations.map((lim, idx) => (
              <li key={idx} style={{ marginBottom: 4 }}>{lim}</li>
            ))}
          </ul>
        </Card>
      )}

      {/* Phase 5: Real API Testing Outcomes */}
      {apiExec && apiExec.total > 0 && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Globe size={18} color="var(--primary)" />
              <h4 style={{ fontWeight: 600, margin: 0 }}>Real API Testing Execution</h4>
              <Badge variant="primary" size="sm">Live HTTPX Execution</Badge>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Badge variant="success" size="sm">{apiExec.passed} Passed</Badge>
              {apiExec.failed > 0 && <Badge variant="danger" size="sm">{apiExec.failed} Failed</Badge>}
              {apiExec.blocked > 0 && <Badge variant="warning" size="sm">{apiExec.blocked} Blocked</Badge>}
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', alignSelf: 'center' }}>
                Duration: {apiExec.durationSeconds}s
              </span>
            </div>
          </div>

          {apiExec.limitation && (
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 12, fontStyle: 'italic' }}>
              Note: {apiExec.limitation}
            </p>
          )}

          <div style={{ overflowX: 'auto' }}>
            <table className="dash-table" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Test Name</th>
                  <th>Method</th>
                  <th>Target URL</th>
                  <th>Status</th>
                  <th>HTTP Code</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {apiExec.tests?.map((t, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 500 }}>{t.name}</td>
                    <td><span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{t.method}</span></td>
                    <td style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{t.url}</td>
                    <td>
                      <Badge
                        variant={t.status === 'PASSED' ? 'success' : t.status === 'BLOCKED' ? 'warning' : 'danger'}
                        size="sm"
                      >
                        {t.status}
                      </Badge>
                    </td>
                    <td>{t.actualStatus || '—'}</td>
                    <td>{t.responseTimeMs ? `${t.responseTimeMs}ms` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Phase 5: Real Security Scanning Outcomes (Bandit + pip-audit) */}
      {secExec && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} color="var(--warning)" />
              <h4 style={{ fontWeight: 600, margin: 0 }}>Real Security Scanning Analysis</h4>
              <Badge variant="warning" size="sm">Bandit & pip-audit Scans</Badge>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Badge variant="danger" size="sm">{secExec.countsBySeverity?.HIGH || 0} High</Badge>
              <Badge variant="warning" size="sm">{secExec.countsBySeverity?.MEDIUM || 0} Medium</Badge>
              <Badge variant="default" size="sm">{secExec.countsBySeverity?.LOW || 0} Low</Badge>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            {secExec.tools && Object.entries(secExec.tools).map(([toolName, toolStat]) => (
              <div
                key={toolName}
                style={{
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--border)',
                  background: 'var(--bg-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 'var(--text-xs)',
                }}
              >
                <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{toolName}:</span>
                {toolStat.available ? (
                  <Badge variant="success" size="sm">
                    {toolStat.executed ? 'Executed' : 'Available'} ({toolStat.version})
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">Unavailable</Badge>
                )}
                {toolStat.error && (
                  <span style={{ color: 'var(--text-muted)' }}>— {toolStat.error}</span>
                )}
              </div>
            ))}
          </div>

          {secExec.findings && secExec.findings.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="dash-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Tool</th>
                    <th>Rule / CVE</th>
                    <th>File & Location</th>
                    <th>Description</th>
                    <th>Remediation</th>
                  </tr>
                </thead>
                <tbody>
                  {secExec.findings.slice(0, 15).map((f, idx) => (
                    <tr key={idx}>
                      <td>
                        <Badge variant={severityVariant[f.severity] || 'default'} size="sm">
                          {f.severity}
                        </Badge>
                      </td>
                      <td style={{ textTransform: 'capitalize', fontWeight: 500 }}>{f.tool}</td>
                      <td><code>{f.ruleId}</code></td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                        {f.file} {f.line ? `(line ${f.line})` : ''}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)' }}>{f.description}</td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                        {f.remediation || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {secExec.findings.length > 15 && (
                <p style={{ textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 8 }}>
                  Showing first 15 of {secExec.findings.length} findings. Full breakdown available in downloaded JSON artifacts.
                </p>
              )}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', margin: 0 }}>
              No vulnerabilities or static security issues detected in scanned scope.
            </p>
          )}
        </Card>
      )}

      {/* Phase 6: RCA and Controlled Self-Healing Summary */}
      {((runData?.rcaDiagnoses && runData.rcaDiagnoses.length > 0) || (runData?.retryHistory && runData.retryHistory.length > 0)) && (
        <Card style={{ marginBottom: 24, borderLeft: '4px solid var(--primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Bot size={18} color="var(--primary)" />
              <h4 style={{ fontWeight: 600, margin: 0 }}>Root Cause Analysis & Controlled Self-Healing</h4>
            </div>
            {runData?.retryHistory?.length > 0 && (
              <Badge variant="success" size="sm">
                {runData.retryHistory.filter(r => r.finalOutcome === 'PASSED_AFTER_RETRY').length} Resolved via Retry
              </Badge>
            )}
          </div>

          {runData?.retryHistory && runData.retryHistory.length > 0 && (
            <div style={{ marginBottom: 16, overflowX: 'auto' }}>
              <h5 style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
                Controlled Retry Controller Log
              </h5>
              <table className="dash-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Test / Action</th>
                    <th>Initial Result</th>
                    <th>Attempts</th>
                    <th>Final Outcome</th>
                    <th>Audit & Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {runData.retryHistory.map((rh, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 500 }}>{rh.testIdentifier}</td>
                      <td><Badge variant="danger" size="sm">{rh.initialResult}</Badge></td>
                      <td>{rh.attemptsCount} / {rh.maxRetriesAllowed}</td>
                      <td>
                        <Badge variant={rh.finalOutcome === 'PASSED_AFTER_RETRY' ? 'success' : 'warning'} size="sm">
                          {rh.finalOutcome}
                        </Badge>
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                        {rh.humanReviewRecommendation || rh.eligibilityReason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {runData?.rcaDiagnoses && runData.rcaDiagnoses.length > 0 && (
            <div>
              <h5 style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
                Evidence-Based Diagnoses ({runData.rcaDiagnoses.length})
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {runData.rcaDiagnoses.map((diag, idx) => (
                  <div key={idx} style={{ padding: 12, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>{diag.failureCategory}</span>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <Badge variant="default" size="sm">{diag.isHypothesis ? 'Hypothesis' : 'Verified Fact'}</Badge>
                        <Badge variant={diag.confidence === 'HIGH' ? 'primary' : 'default'} size="sm">{diag.confidence} Confidence</Badge>
                      </div>
                    </div>
                    <p style={{ margin: '4px 0', fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>{diag.rootCauseHypothesis}</p>
                    <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                      <strong>Action:</strong> {diag.recommendedAction}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Generated Artifacts */}
      {runData?.artifacts && Object.keys(runData.artifacts).length > 0 && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Paperclip size={18} />
            <h4 style={{ fontWeight: 600, margin: 0 }}>Generated Pipeline Artifacts</h4>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(runData.artifacts).map(([fname]) => (
              <a
                key={fname}
                href={testRunApi.getArtifactUrl(runId, fname)}
                target="_blank"
                rel="noreferrer"
                download={fname}
                style={{ textDecoration: 'none' }}
              >
                <Button variant="ghost" size="sm" leftIcon={FileCode}>
                  {fname}
                </Button>
              </a>
            ))}
          </div>
        </Card>
      )}

      {/* Final Markdown Report Viewer */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontWeight: 600 }}>Test Report</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Button variant="primary" size="sm" leftIcon={Download} onClick={handleDownload}>
              Download (.md)
            </Button>
            {runId && (
              <a
                href={`/api/runs/${runId}/report?format=html`}
                target="_blank"
                rel="noreferrer"
                style={{ textDecoration: 'none' }}
              >
                <Button variant="secondary" size="sm">
                  Print / Save as PDF
                </Button>
              </a>
            )}
            <Button variant="ghost" size="sm" leftIcon={Copy} onClick={handleCopy}>
              Copy Markdown
            </Button>
          </div>
        </div>
        <MarkdownViewer content={reportText} />
      </Card>

      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <Link to="/console"><Button variant="ghost" leftIcon={Terminal}>View Logs</Button></Link>
        <Link to="/projects"><Button variant="ghost" leftIcon={Play}>Back to Projects</Button></Link>
      </div>
    </div>
  );
}
