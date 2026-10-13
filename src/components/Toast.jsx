import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import './Toast.css';

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="toast-container">
      <AnimatePresence>
        {toasts.slice(-5).map((toast) => {
          const Icon = icons[toast.type] || Info;
          return (
            <motion.div
              key={toast.id}
              className={`toast toast--${toast.type} ${toast.removing ? 'toast--removing' : ''}`}
              initial={{ opacity: 0, x: 100, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.9 }}
              transition={{ type: 'spring', duration: 0.4 }}
            >
              <Icon size={18} className="toast__icon" />
              <span className="toast__message">{toast.message}</span>
              <button className="toast__close" onClick={() => removeToast(toast.id)} aria-label="Close">
                <X size={14} />
              </button>
              <div className="toast__progress" />
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
