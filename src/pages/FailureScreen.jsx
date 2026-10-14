import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { XCircle, RotateCcw, Bug, Download, Terminal, ArrowLeft, ChevronDown, ChevronRight, Image } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import CodeBlock from '../components/CodeBlock';
import { mockErrorTrace } from '../data/mockData';
import { testRunApi } from '../services/api';
import './FailureScreen.css';

export default function FailureScreen() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const runId = searchParams.get('runId');

  const [expandTrace, setExpandTrace] = useState(true);
  const [runData, setRunData] = useState(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (!runId) return;

    let isMounted = true;
    testRunApi.getRunStatus(runId).then(data => {
      if (isMounted && data) {
        setRunData(data);
      }
    }).catch(err => {
      console.error('Failed to load failed run details:', err);
    });

    return () => {
      isMounted = false;
    };
  }, [runId]);

  const handleRetry = async () => {
    if (!runId) return;
    try {
      setRetrying(true);
      const newRun = await testRunApi.restartRun(runId);
      navigate(`/run-monitor?runId=${newRun.id || newRun.runId}`);
    } catch (err) {
      alert(err.message || 'Failed to retry run');
    } finally {
      setRetrying(false);
    }
  };

  const handleDownloadLog = () => {
    const content = runData?.errorTrace || mockErrorTrace;
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `error-trace-${runId || 'run'}.log`;
    a.click();
  };

  const errorTrace = runData?.errorTrace || mockErrorTrace;
  const projectTitle = runData?.projectName || 'Multi-Agent Test Pipeline';
  const failedStage = runData?.currentStage || `Step ${runData?.stepsCompleted || 5} of 9`;
  const durationSec = runData?.duration || 0;
  const durationStr = `${Math.floor(durationSec / 60)}m ${durationSec % 60}s`;

  // Check for screenshot
  const screenshotName = runData?.screenshots?.[0] || (runData?.artifacts && Object.keys(runData.artifacts).find(k => k.endsWith('.png')));
  const screenshotUrl = screenshotName && runId ? testRunApi.getArtifactUrl(runId, screenshotName) : null;

  return (
    <div className="failure-page">
      <motion.div className="failure-header" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}>
          <XCircle size={72} color="var(--danger)" strokeWidth={1.5} />
        </motion.div>
        <h1 className="failure-header__title">Test Run Terminated / Failed</h1>
        <p className="failure-header__subtitle">{projectTitle} — {failedStage}</p>
      </motion.div>

      <Card className="failure-summary">
        <div className="failure-summary__grid">
          <div>
            <span className="failure-summary__label">Status</span>
            <span className="failure-summary__value failure-summary__value--danger">
              {(runData?.status || 'FAILED').toUpperCase()}
            </span>
          </div>
          <div>
            <span className="failure-summary__label">Failed Stage</span>
            <span className="failure-summary__value">{failedStage}</span>
          </div>
          <div>
            <span className="failure-summary__label">Steps Completed</span>
            <span className="failure-summary__value">{runData?.stepsCompleted || 0} / 9</span>
          </div>
          <div>
            <span className="failure-summary__label">Duration</span>
            <span className="failure-summary__value">{durationStr}</span>
          </div>
        </div>
      </Card>

      <Card padding="none" className="failure-trace-card">
        <button className="failure-trace-toggle" onClick={() => setExpandTrace(!expandTrace)}>
          {expandTrace ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <span>Stack Trace & Error Details</span>
        </button>
        {expandTrace && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}>
            <CodeBlock code={errorTrace} language="log" />
          </motion.div>
        )}
      </Card>

      {screenshotUrl ? (
        <Card className="failure-screenshot">
          <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Image size={16} /> Playwright Failure Screenshot
          </h4>
          <div style={{ textAlign: 'center' }}>
            <img
              src={screenshotUrl}
              alt="Playwright Failure Screenshot"
              style={{ maxWidth: '100%', maxHeight: '400px', borderRadius: 8, border: '1px solid var(--border)' }}
            />
          </div>
        </Card>
      ) : (
        <Card className="failure-screenshot">
          <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Image size={16} /> Playwright Screenshot
          </h4>
          <div className="failure-screenshot__area">
            <div className="failure-screenshot__placeholder">
              <Image size={48} strokeWidth={1} />
              <span>No failure screenshot captured for this run.</span>
            </div>
          </div>
        </Card>
      )}

      {/* Phase 6: Intelligent Root Cause Diagnoses & Controlled Self-Healing Recommendations */}
      {((runData?.rcaDiagnoses && runData.rcaDiagnoses.length > 0) || (runData?.findings?.rcaDiagnoses && runData.findings.rcaDiagnoses.length > 0)) && (
        <Card style={{ marginTop: 20, borderLeft: '4px solid var(--danger)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Bug size={18} color="var(--danger)" />
            <h4 style={{ fontWeight: 600, margin: 0 }}>Intelligent Root Cause Diagnosis & Evidence Analysis</h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {(runData.rcaDiagnoses || runData.findings.rcaDiagnoses).map((diag, idx) => (
              <div
                key={idx}
                style={{
                  padding: 14,
                  borderRadius: 8,
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--danger)' }}>
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

                {diag.supportingEvidence && diag.supportingEvidence.length > 0 && (
                  <div style={{ margin: '8px 0', padding: 8, borderRadius: 4, background: 'var(--bg-primary)', fontSize: 'var(--text-xs)' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Supporting Evidence:</span>
                    <ul style={{ margin: '4px 0 0 0', paddingLeft: 18, color: 'var(--text-muted)' }}>
                      {diag.supportingEvidence.map((ev, eIdx) => (
                        <li key={eIdx}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div style={{ marginTop: 8, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  <strong style={{ color: 'var(--primary)' }}>Recommended Human Action:</strong> {diag.recommendedAction}
                  <div style={{ marginTop: 4, fontStyle: 'italic', color: 'var(--text-muted)' }}>
                    Note: Autonomous code modifications are strictly prohibited by policy; human review required.
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Phase 5: Partial API and Security findings if run failed */}
      {(runData?.apiExecution || runData?.findings?.apiExecution) && (
        <Card style={{ marginTop: 12 }}>
          <h4 style={{ fontWeight: 600, marginBottom: 8 }}>API Test Results Before Failure</h4>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', margin: 0 }}>
            Executed: {(runData.apiExecution || runData.findings.apiExecution).total} requests (
            {(runData.apiExecution || runData.findings.apiExecution).passed} passed,{' '}
            {(runData.apiExecution || runData.findings.apiExecution).failed} failed,{' '}
            {(runData.apiExecution || runData.findings.apiExecution).blocked} blocked)
          </p>
        </Card>
      )}

      {(runData?.securityExecution || runData?.findings?.securityExecution) && (
        <Card style={{ marginTop: 12 }}>
          <h4 style={{ fontWeight: 600, marginBottom: 8 }}>Security Findings (Bandit & pip-audit)</h4>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', margin: 0 }}>
            Total Findings: {(runData.securityExecution || runData.findings.securityExecution).totalFindings} (
            High: {(runData.securityExecution || runData.findings.securityExecution).countsBySeverity?.HIGH || 0}, Medium:{' '}
            {(runData.securityExecution || runData.findings.securityExecution).countsBySeverity?.MEDIUM || 0}, Low:{' '}
            {(runData.securityExecution || runData.findings.securityExecution).countsBySeverity?.LOW || 0})
          </p>
        </Card>
      )}

      <div className="failure-actions">
        {runId && (
          <Button variant="primary" leftIcon={RotateCcw} loading={retrying} onClick={handleRetry}>
            Retry Run
          </Button>
        )}
        <Button variant="ghost" leftIcon={Download} onClick={handleDownloadLog}>
          Download Error Log
        </Button>
        <Link to="/console"><Button variant="ghost" leftIcon={Terminal}>View Full Logs</Button></Link>
        <Link to="/projects"><Button variant="ghost" leftIcon={ArrowLeft}>Back to Projects</Button></Link>
      </div>
    </div>
  );
}
