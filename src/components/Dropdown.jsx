import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import './Dropdown.css';

export default function Dropdown({ trigger, items, align = 'left', className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    if (isOpen) document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  return (
    <div className={`dropdown ${className}`} ref={ref}>
      <button className="dropdown__trigger" onClick={() => setIsOpen(!isOpen)}>
        {trigger}
        <ChevronDown size={16} className={`dropdown__chevron ${isOpen ? 'dropdown__chevron--open' : ''}`} />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={`dropdown__panel dropdown__panel--${align}`}
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
          >
            {items.map((item, i) =>
              item.divider ? (
                <div key={i} className="dropdown__divider" />
              ) : (
                <button
                  key={i}
                  className={`dropdown__item ${item.danger ? 'dropdown__item--danger' : ''} ${item.active ? 'dropdown__item--active' : ''}`}
                  onClick={() => { item.onClick?.(); setIsOpen(false); }}
                >
                  {item.icon && <item.icon size={16} className="dropdown__item-icon" />}
                  <span>{item.label}</span>
                </button>
              )
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
