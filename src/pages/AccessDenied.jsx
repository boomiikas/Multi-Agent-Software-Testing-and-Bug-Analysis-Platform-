import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ShieldOff } from 'lucide-react';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';
import './NotFound.css';

export default function AccessDenied() {
  const { isAdmin } = useAuth();

  return (
    <div className="not-found">
      <div className="nf-bg-shapes">
        <div className="nf-shape nf-shape--1" />
        <div className="nf-shape nf-shape--2" />
        <div className="nf-shape nf-shape--3" />
      </div>
      <motion.div className="nf-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
          <ShieldOff size={72} color="var(--danger)" />
        </div>
        <h1 className="nf-title">403 — Access Denied</h1>
        <p className="nf-desc">You don't have permission to view this page. This area is restricted to administrators.</p>
        <div className="nf-actions">
          <Link to={isAdmin ? '/admin/users' : '/dashboard'}><Button variant="primary" size="lg">Go Home</Button></Link>
          <Button variant="ghost" size="lg" leftIcon={ArrowLeft} onClick={() => window.history.back()}>Go Back</Button>
        </div>
      </motion.div>
    </div>
  );
}
