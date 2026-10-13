import './ProgressBar.css';

export default function ProgressBar({ value = 0, max = 100, variant = 'primary', showLabel = false, striped = false, size = 'md', className = '' }) {
  const percent = Math.min(Math.max((value / max) * 100, 0), 100);

  const classes = [
    'progress',
    `progress--${variant}`,
    `progress--${size}`,
    striped && 'progress--striped',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={classes}>
      <div className="progress__track">
        <div className="progress__fill" style={{ width: `${percent}%` }} />
      </div>
      {showLabel && <span className="progress__label">{Math.round(percent)}%</span>}
    </div>
  );
}
