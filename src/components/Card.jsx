import { motion } from 'framer-motion';
import './Card.css';

export default function Card({
  children,
  variant = 'default',
  padding = 'md',
  clickable = false,
  hoverable = true,
  glowing = false,
  className = '',
  onClick,
  ...props
}) {
  const classes = [
    'card',
    `card--${variant}`,
    `card--pad-${padding}`,
    clickable && 'card--clickable',
    hoverable && 'card--hoverable',
    glowing && 'card--glowing',
    className,
  ].filter(Boolean).join(' ');

  return (
    <motion.div
      className={classes}
      onClick={onClick}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
