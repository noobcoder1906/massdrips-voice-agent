import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'accent';
  size?: 'sm' | 'md';
  dot?: boolean;
}

const variants = {
  success: { bg: 'rgba(0,229,153,0.12)', text: '#00e599', border: 'rgba(0,229,153,0.25)' },
  warning: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b', border: 'rgba(245,158,11,0.25)' },
  error: { bg: 'rgba(239,68,68,0.12)', text: '#ef4444', border: 'rgba(239,68,68,0.25)' },
  info: { bg: 'rgba(99,102,241,0.12)', text: '#6366f1', border: 'rgba(99,102,241,0.25)' },
  neutral: { bg: 'rgba(144,144,168,0.1)', text: '#9090a8', border: 'rgba(144,144,168,0.2)' },
  accent: { bg: 'rgba(0,229,153,0.12)', text: '#00e599', border: 'rgba(0,229,153,0.3)' },
};

export default function Badge({ children, variant = 'neutral', size = 'md', dot = false }: BadgeProps) {
  const v = variants[variant];
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full ${size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'}`}
      style={{ background: v.bg, color: v.text, border: `1px solid ${v.border}` }}
    >
      {dot && (
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ background: v.text }}
        />
      )}
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    active: { variant: 'success', label: 'Active' },
    paused: { variant: 'warning', label: 'Paused' },
    draft: { variant: 'neutral', label: 'Draft' },
    completed: { variant: 'info', label: 'Completed' },
    hot: { variant: 'error', label: 'Hot' },
    warm: { variant: 'warning', label: 'Warm' },
    cold: { variant: 'info', label: 'Cold' },
    converted: { variant: 'success', label: 'Converted' },
    interested: { variant: 'accent', label: 'Interested' },
    not_interested: { variant: 'error', label: 'Not Interested' },
    callback: { variant: 'warning', label: 'Callback' },
    positive: { variant: 'success', label: 'Positive' },
    very_positive: { variant: 'success', label: 'Very Positive' },
    negative: { variant: 'error', label: 'Negative' },
    neutral: { variant: 'neutral', label: 'Neutral' },
    low_stock: { variant: 'warning', label: 'Low Stock' },
  };

  const config = map[status] ?? { variant: 'neutral', label: status };
  return <Badge variant={config.variant} dot>{config.label}</Badge>;
}
