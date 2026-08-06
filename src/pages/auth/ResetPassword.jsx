import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, CheckCircle, AlertCircle, KeyRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Input from '../../components/Input';
import './ForgotPassword.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const { resetPassword } = useAuth();
  const navigate = useNavigate();

  const validate = () => {
    if (!token) return 'This reset link is missing its token. Request a new one.';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(password) || !/[0-9]/.test(password)) return 'Password needs an uppercase letter and a number';
    if (password !== confirmPassword) return 'Passwords do not match';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const err = validate();
    if (err) { setError(err); return; }
    setLoading(true);
    const result = await resetPassword(token, password);
    setLoading(false);
    if (result.success) setDone(true);
    else setError(result.error || 'Something went wrong. Please try again.');
  };

  return (
    <div className="forgot-page">
      <motion.div className="forgot-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {!done ? (
          <>
            <div className="forgot-card__icon"><KeyRound size={28} /></div>
            <h1 className="forgot-card__title">Set a new password</h1>
            <p className="forgot-card__subtitle">Choose a new password for your account</p>
            {error && <div className="auth-form__error"><AlertCircle size={16} /> {error}</div>}
            <form onSubmit={handleSubmit} className="forgot-card__form">
              <Input label="New Password" type="password" placeholder="Min. 8 characters" value={password} onChange={e => setPassword(e.target.value)} leftIcon={Lock} />
              <Input label="Confirm Password" type="password" placeholder="Re-enter password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} leftIcon={Lock} />
              <Button type="submit" variant="primary" fullWidth loading={loading} size="lg">Reset Password</Button>
            </form>
            <Link to="/login" className="forgot-card__back">← Back to Login</Link>
          </>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="forgot-card__success">
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}>
              <CheckCircle size={64} color="var(--success)" />
            </motion.div>
            <h2 className="forgot-card__title">Password updated</h2>
            <p className="forgot-card__subtitle">You can now sign in with your new password.</p>
            <Button variant="primary" size="lg" onClick={() => navigate('/login')}>Back to Login</Button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
