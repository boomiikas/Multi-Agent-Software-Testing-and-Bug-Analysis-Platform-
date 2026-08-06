import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Button from '../components/Button';
import { ArrowLeft } from 'lucide-react';
import './NotFound.css';

export default function NotFound() {
  return (
    <div className="not-found">
      <div className="nf-bg-shapes">
        <div className="nf-shape nf-shape--1" />
        <div className="nf-shape nf-shape--2" />
        <div className="nf-shape nf-shape--3" />
      </div>
      <motion.div className="nf-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="nf-code">404</h1>
        <h2 className="nf-title">Page Not Found</h2>
        <p className="nf-desc">The page you're looking for doesn't exist or has been moved.</p>
        <div className="nf-actions">
          <Link to="/dashboard"><Button variant="primary" size="lg">Go Home</Button></Link>
          <Button variant="ghost" size="lg" leftIcon={ArrowLeft} onClick={() => window.history.back()}>Go Back</Button>
        </div>
      </motion.div>
    </div>
  );
}
