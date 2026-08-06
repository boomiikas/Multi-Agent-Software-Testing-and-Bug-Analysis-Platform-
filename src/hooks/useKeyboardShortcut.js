import { useEffect, useCallback } from 'react';

export function useKeyboardShortcut(key, callback, modifiers = {}) {
  const handleKeyDown = useCallback((event) => {
    const { ctrlKey = false, metaKey = false, shiftKey = false, altKey = false } = modifiers;
    
    const ctrlOrMeta = ctrlKey || metaKey;
    const isModifierMatch = ctrlOrMeta
      ? (event.ctrlKey || event.metaKey)
      : true;
    
    if (
      event.key.toLowerCase() === key.toLowerCase() &&
      isModifierMatch &&
      event.shiftKey === shiftKey &&
      event.altKey === altKey
    ) {
      event.preventDefault();
      callback(event);
    }
  }, [key, callback, modifiers]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
