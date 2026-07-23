import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  className?: string;
}

const variants = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
};

export default function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}

export function statusVariant(status: string): BadgeProps['variant'] {
  const map: Record<string, BadgeProps['variant']> = {
    idle: 'info',
    busy: 'warning',
    active: 'success',
    inactive: 'default',
    error: 'danger',
    offline: 'default',
    maintenance: 'warning',
    healthy: 'success',
    degraded: 'warning',
    down: 'danger',
    pending: 'info',
    queued: 'default',
    assigned: 'info',
    in_progress: 'warning',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'default',
    timeout: 'danger',
    retrying: 'info',
    low: 'default',
    normal: 'info',
    medium: 'info',
    high: 'warning',
    urgent: 'danger',
    critical: 'danger',
  };
  return map[status] || 'default';
}
