import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Hexagon, Mail, Lock, CheckCircle, Shield, Zap, Globe, AlertCircle, User, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Input from '../../components/Input';
import './Login.css';

export default function Login() {
  const [loginType, setLoginType] = useState('user'); // 'user' | 'admin' — purely a UX guard, role always comes from the account itself
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const { login, logout, isLoading } = useAuth();
  const navigate = useNavigate();

  const validate = () => {
    if (!email) return 'Email is required';
    if (!/\S+@\S+\.\S+/.test(email)) return 'Enter a valid email';
    if (!password) return 'Password is required';
    if (password.length < 6) return 'Password must be at least 6 characters';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const err = validate();
    if (err) { setError(err); return; }
    const result = await login(email, password, rememberMe);
    if (!result.success) { setError(result.error); return; }

    const actualRole = result.user?.role; // 'ADMIN' | 'USER'
    const expectedRole = loginType === 'admin' ? 'ADMIN' : 'USER';
    if (actualRole !== expectedRole) {
      logout();
      setError(
        actualRole === 'ADMIN'
          ? 'This is an admin account. Switch to the Admin tab to sign in.'
          : 'This is a user account. Switch to the User tab to sign in.'
      );
      return;
    }

    navigate(actualRole === 'ADMIN' ? '/admin/users' : '/dashboard');
  };

  return (
    <div className="auth-layout">
      <div className="auth-layout__illustration">
        <motion.div className="auth-illustration" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8 }}>
          <div className="auth-illustration__graphic">
            <div className="auth-illustration__orbit auth-illustration__orbit--1" />
            <div className="auth-illustration__orbit auth-illustration__orbit--2" />
            <div className="auth-illustration__orbit auth-illustration__orbit--3" />
            <div className="auth-illustration__center"><Hexagon size={28} /></div>
            <div className="auth-illustration__node auth-illustration__node--1"><CheckCircle size={16} /></div>
            <div className="auth-illustration__node auth-illustration__node--2"><Shield size={16} /></div>
            <div className="auth-illustration__node auth-illustration__node--3"><Zap size={16} /></div>
            <div className="auth-illustration__node auth-illustration__node--4"><Globe size={16} /></div>
          </div>
          <h2 className="auth-illustration__title">AI-Powered Testing</h2>
          <p className="auth-illustration__description">
            Deploy multi-agent AI systems to automatically test your web applications with enterprise-grade reliability.
          </p>
        </motion.div>
      </div>

      <div className="auth-layout__form">
        <motion.form className="auth-form" onSubmit={handleSubmit} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
          <div className="auth-form__logo">
            <div className="auth-form__logo-icon"><Hexagon size={22} /></div>
            <span className="auth-form__logo-text">AgentQA</span>
          </div>
          <h1 className="auth-form__title">Welcome back</h1>
          <p className="auth-form__subtitle">Sign in to your account to continue</p>

          <div className="auth-form__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={loginType === 'user'}
              className={`auth-form__tab ${loginType === 'user' ? 'auth-form__tab--active' : ''}`}
              onClick={() => { setLoginType('user'); setError(''); }}
            >
              <User size={15} /> User
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={loginType === 'admin'}
              className={`auth-form__tab ${loginType === 'admin' ? 'auth-form__tab--active' : ''}`}
              onClick={() => { setLoginType('admin'); setError(''); }}
            >
              <ShieldCheck size={15} /> Admin
            </button>
          </div>

          {error && (
            <div className="auth-form__error"><AlertCircle size={16} /> {error}</div>
          )}

          <div className="auth-form__fields">
            <Input label="Email" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} leftIcon={Mail} autoComplete="email" />
            <Input label="Password" type="password" placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} leftIcon={Lock} autoComplete="current-password" />
          </div>

          <div className="auth-form__footer">
            <label className="auth-form__remember">
              <input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} />
              Remember me
            </label>
            <Link to="/forgot-password">Forgot password?</Link>
          </div>

          <Button type="submit" variant="primary" fullWidth loading={isLoading} size="lg" style={{ marginTop: 24 }}>
            Sign In
          </Button>

          <div className="auth-form__divider">or continue with</div>

          <div style={{ display: 'flex', gap: 12 }}>
            <Button variant="secondary" fullWidth>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              GitHub
            </Button>
            <Button variant="secondary" fullWidth>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Google
            </Button>
          </div>

          <p className="auth-form__link">
            Don't have an account? <Link to="/register">Sign up</Link>
          </p>
        </motion.form>
      </div>
    </div>
  );
}
