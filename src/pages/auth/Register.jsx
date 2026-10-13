import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Hexagon, Mail, Lock, User, AlertCircle, CheckCircle, Shield, Zap, Globe } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Input from '../../components/Input';
import './Register.css';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState('');
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();

  const getPasswordStrength = () => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };

  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['', 'var(--danger)', 'var(--warning)', 'var(--primary)', 'var(--success)'];
  const strength = getPasswordStrength();

  const validate = () => {
    if (!name || name.length < 2) return 'Name is required';
    if (!email || !/\S+@\S+\.\S+/.test(email)) return 'Enter a valid email';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (password !== confirmPassword) return 'Passwords do not match';
    if (!terms) return 'You must agree to the Terms of Service';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const err = validate();
    if (err) { setError(err); return; }
    const result = await register(name, email, password);
    if (result.success) navigate('/dashboard');
    else setError(result.error || 'Registration failed');
    // Registered accounts are always role USER — admin accounts are seeded
    // or created by an existing admin in Manage Users, never via this form.
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
          <h2 className="auth-illustration__title">Join AgentQA</h2>
          <p className="auth-illustration__description">Start testing your web applications with AI-powered multi-agent systems today.</p>
        </motion.div>
      </div>

      <div className="auth-layout__form">
        <motion.form className="auth-form" onSubmit={handleSubmit} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <div className="auth-form__logo">
            <div className="auth-form__logo-icon"><Hexagon size={22} /></div>
            <span className="auth-form__logo-text">AgentQA</span>
          </div>
          <h1 className="auth-form__title">Create your account</h1>
          <p className="auth-form__subtitle">Get started with a free account</p>

          {error && <div className="auth-form__error"><AlertCircle size={16} /> {error}</div>}

          <div className="auth-form__fields">
            <Input label="Full Name" placeholder="John Doe" value={name} onChange={e => setName(e.target.value)} leftIcon={User} />
            <Input label="Email" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} leftIcon={Mail} />
            <div>
              <Input label="Password" type="password" placeholder="Min. 8 characters" value={password} onChange={e => setPassword(e.target.value)} leftIcon={Lock} />
              {password && (
                <div className="register__strength">
                  <div className="register__strength-bar">
                    {[1,2,3,4].map(i => (
                      <div key={i} className="register__strength-segment" style={{ background: i <= strength ? strengthColors[strength] : 'var(--bg-surface-hover)' }} />
                    ))}
                  </div>
                  <span className="register__strength-label" style={{ color: strengthColors[strength] }}>{strengthLabels[strength]}</span>
                </div>
              )}
            </div>
            <Input label="Confirm Password" type="password" placeholder="Re-enter password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} leftIcon={Lock} />
          </div>

          <label className="auth-form__remember" style={{ marginTop: 16 }}>
            <input type="checkbox" checked={terms} onChange={e => setTerms(e.target.checked)} />
            I agree to the Terms of Service and Privacy Policy
          </label>

          <Button type="submit" variant="primary" fullWidth loading={isLoading} size="lg" style={{ marginTop: 24 }}>Create Account</Button>

          <p className="auth-form__link">Already have an account? <Link to="/login">Sign in</Link></p>
        </motion.form>
      </div>
    </div>
  );
}
