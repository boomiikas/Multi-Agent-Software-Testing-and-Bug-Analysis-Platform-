import { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import './Button.css';

const Button = forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  loading = false,
  disabled = false,
  fullWidth = false,
  type = 'button',
  className = '',
  onClick,
  ...props
}, ref) => {
  const classes = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    fullWidth && 'btn--full',
    loading && 'btn--loading',
    className,
  ].filter(Boolean).join(' ');

  return (
    <motion.button
      ref={ref}
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      {...props}
    >
      {loading && <Loader2 className="btn__spinner" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
      {!loading && LeftIcon && <LeftIcon className="btn__icon" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
      {children && <span className="btn__label">{children}</span>}
      {!loading && RightIcon && <RightIcon className="btn__icon" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
    </motion.button>
  );
});

Button.displayName = 'Button';
export default Button;
