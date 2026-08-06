import { FolderOpen } from 'lucide-react';
import Button from './Button';
import './EmptyState.css';

export default function EmptyState({ icon: Icon = FolderOpen, title, description, actionLabel, onAction, className = '' }) {
  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state__icon-wrap">
        <Icon size={48} strokeWidth={1} />
      </div>
      <h3 className="empty-state__title">{title}</h3>
      {description && <p className="empty-state__desc">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
