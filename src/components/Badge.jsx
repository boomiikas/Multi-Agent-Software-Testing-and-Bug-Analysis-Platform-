import './Badge.css';

export default function Badge({ children, variant = 'default', size = 'md', dot = false, pulse = false, className = '' }) {
  const classes = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    dot && 'badge--dot',
    pulse && 'badge--pulse',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={classes}>
      {dot && <span className="badge__dot" />}
      {children}
    </span>
  );
}
