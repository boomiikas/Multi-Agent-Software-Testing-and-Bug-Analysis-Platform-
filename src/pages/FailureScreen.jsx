import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { XCircle, RotateCcw, Bug, Download, Terminal, ArrowLeft, ChevronDown, ChevronRight, Image } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import CodeBlock from '../components/CodeBlock';
import { mockErrorTrace } from '../data/mockData';
import './FailureScreen.css';

export default function FailureScreen() {
  const [expandTrace, setExpandTrace] = useState(false);

  return (
    <div className="failure-page">
      <motion.div className="failure-header" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}>
          <XCircle size={72} color="var(--danger)" strokeWidth={1.5} />
        </motion.div>
        <h1 className="failure-header__title">Test Run Failed</h1>
        <p className="failure-header__subtitle">E-Commerce Checkout Flow — Step 6: Execute Tests</p>
      </motion.div>

      <Card className="failure-summary">
        <div className="failure-summary__grid">
          <div><span className="failure-summary__label">Error Type</span><span className="failure-summary__value failure-summary__value--danger">AssertionError</span></div>
          <div><span className="failure-summary__label">Message</span><span className="failure-summary__value">Cart persistence test failed</span></div>
          <div><span className="failure-summary__label">Failed At</span><span className="failure-summary__value">Step 6 of 9</span></div>
          <div><span className="failure-summary__label">Duration</span><span className="failure-summary__value">15m 00s</span></div>
        </div>
      </Card>

      <Card padding="none" className="failure-trace-card">
        <button className="failure-trace-toggle" onClick={() => setExpandTrace(!expandTrace)}>
          {expandTrace ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <span>Stack Trace</span>
        </button>
        {expandTrace && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}>
            <CodeBlock code={mockErrorTrace} language="stack trace" />
          </motion.div>
        )}
      </Card>

      <Card className="failure-screenshot">
        <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}><Image size={16} /> Playwright Screenshot</h4>
        <div className="failure-screenshot__area">
          <div className="failure-screenshot__placeholder">
            <Image size={48} strokeWidth={1} />
            <span>checkout-page-error.png</span>
            <Button variant="ghost" size="sm" leftIcon={Download}>Download</Button>
          </div>
        </div>
      </Card>

      <div className="failure-actions">
        <Button variant="primary" leftIcon={RotateCcw}>Retry Run</Button>
        <Button variant="secondary" leftIcon={Bug}>Report Bug</Button>
        <Button variant="ghost" leftIcon={Download}>Download Error Log</Button>
        <Link to="/console"><Button variant="ghost" leftIcon={Terminal}>View Full Logs</Button></Link>
        <Link to="/projects"><Button variant="ghost" leftIcon={ArrowLeft}>Back to Projects</Button></Link>
      </div>
    </div>
  );
}
