import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import './Input.css';

export default function Input({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  helperText,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  disabled = false,
  required = false,
  fullWidth = true,
  className = '',
  id,
  name,
  autoComplete,
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  const wrapperClasses = [
    'input-wrapper',
    fullWidth && 'input-wrapper--full',
    error && 'input-wrapper--error',
    disabled && 'input-wrapper--disabled',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={wrapperClasses}>
      {label && (
        <label className="input__label" htmlFor={id || name}>
          {label}
          {required && <span className="input__required">*</span>}
        </label>
      )}
      <div className="input__container">
        {LeftIcon && (
          <span className="input__icon input__icon--left">
            <LeftIcon size={18} />
          </span>
        )}
        <input
          id={id || name}
          name={name}
          type={inputType}
          className="input__field"
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          autoComplete={autoComplete}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            className="input__toggle"
            onClick={() => setShowPassword(!showPassword)}
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
        {!isPassword && RightIcon && (
          <span className="input__icon input__icon--right">
            <RightIcon size={18} />
          </span>
        )}
      </div>
      {error && <span className="input__error">{error}</span>}
      {!error && helperText && <span className="input__helper">{helperText}</span>}
    </div>
  );
}
