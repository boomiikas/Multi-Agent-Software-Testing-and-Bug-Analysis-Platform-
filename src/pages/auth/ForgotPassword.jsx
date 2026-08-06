import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, Mail, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Input from '../../components/Input';
import './ForgotPassword.css';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [devResetLink, setDevResetLink] = useState(null);
  const { forgotPassword } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email || !/\S+@\S+\.\S+/.test(email)) { setError('Enter a valid email'); return; }
    setLoading(true);
    const result = await forgotPassword(email);
    setLoading(false);
    if (result.success) {
      setSent(true);
      // No email provider is configured for this project, so in dev the
      // API hands back the reset token directly instead of emailing it.
      if (result.resetTokenForDev) {
        setDevResetLink(`/reset-password?token=${result.resetTokenForDev}`);
      }
    } else {
      setError(result.error || 'Something went wrong. Please try again.');
    }
  };

  return (
    <div className="forgot-page">
      <motion.div className="forgot-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {!sent ? (
          <>
            <div className="forgot-card__icon"><Lock size={28} /></div>
            <h1 className="forgot-card__title">Forgot your password?</h1>
            <p className="forgot-card__subtitle">Enter your email and we'll send you a reset link</p>
            {error && <div className="auth-form__error"><AlertCircle size={16} /> {error}</div>}
            <form onSubmit={handleSubmit} className="forgot-card__form">
              <Input label="Email" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} leftIcon={Mail} />
              <Button type="submit" variant="primary" fullWidth loading={loading} size="lg">Send Reset Link</Button>
            </form>
            <Link to="/login" className="forgot-card__back">← Back to Login</Link>
          </>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="forgot-card__success">
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}>
              <CheckCircle size={64} color="var(--success)" />
            </motion.div>
            <h2 className="forgot-card__title">Check your email</h2>
            <p className="forgot-card__subtitle">We sent a reset link to <strong>{email}</strong></p>
            {devResetLink && (
              <p className="forgot-card__subtitle" style={{ fontSize: 13 }}>
                No email service is configured yet — for local testing, use this link directly:{' '}
                <Link to={devResetLink}>Reset password</Link>
              </p>
            )}
            <Link to="/login"><Button variant="primary" size="lg">Back to Login</Button></Link>
            <button className="forgot-card__resend" onClick={() => setSent(false)}>Didn't receive it? Resend</button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
