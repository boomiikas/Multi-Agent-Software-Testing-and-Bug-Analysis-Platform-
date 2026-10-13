import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Tooltip.css';

export default function Tooltip({ children, content, position = 'top', delay = 300 }) {
  const [show, setShow] = useState(false);
  const [timeout, setTimeoutId] = useState(null);

  const handleEnter = () => {
    const id = setTimeout(() => setShow(true), delay);
    setTimeoutId(id);
  };

  const handleLeave = () => {
    clearTimeout(timeout);
    setShow(false);
  };

  return (
    <div className="tooltip-wrapper" onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      {children}
      <AnimatePresence>
        {show && (
          <motion.div
            className={`tooltip tooltip--${position}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.15 }}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
