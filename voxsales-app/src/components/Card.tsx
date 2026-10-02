import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export default function Card({ children, className = '', hover = false, onClick, style }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl p-5 transition-all duration-200 ${hover ? 'hover:border-white/15 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer' : ''} ${className}`}
      style={{
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
      {children}
    </h3>
  );
}
