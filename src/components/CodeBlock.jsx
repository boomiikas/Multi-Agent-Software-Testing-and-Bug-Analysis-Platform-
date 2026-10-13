import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import './CodeBlock.css';

export default function CodeBlock({ code, language = 'log', showLineNumbers = true, className = '' }) {
  const [copied, setCopied] = useState(false);
  const lines = code.split('\n');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const colorLine = (line) => {
    if (line.includes('ERROR') || line.includes('FAILED') || line.includes('Error')) return 'code-line--error';
    if (line.includes('SUCCESS') || line.includes('passed') || line.includes('✓')) return 'code-line--success';
    if (line.includes('WARN') || line.includes('warning')) return 'code-line--warning';
    if (line.includes('DEBUG')) return 'code-line--debug';
    return '';
  };

  return (
    <div className={`code-block ${className}`}>
      <div className="code-block__header">
        <span className="code-block__lang">{language}</span>
        <button className="code-block__copy" onClick={handleCopy} aria-label="Copy code">
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="code-block__pre">
        <code>
          {lines.map((line, i) => (
            <div key={i} className={`code-line ${colorLine(line)}`}>
              {showLineNumbers && <span className="code-line__number">{i + 1}</span>}
              <span className="code-line__content">{line}</span>
            </div>
          ))}
        </code>
      </pre>
    </div>
  );
}
