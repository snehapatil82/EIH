import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'cyan';
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  dot = false,
  className = '',
}) => {
  const variantStyles = {
    default: 'bg-slate-800/90 text-slate-300 border-slate-700/80 shadow-sm',
    success: 'bg-emerald-950/70 text-emerald-300 border-emerald-500/30 shadow-[0_0_12px_-3px_rgba(16,185,129,0.2)]',
    warning: 'bg-amber-950/70 text-amber-300 border-amber-500/30 shadow-[0_0_12px_-3px_rgba(245,158,11,0.2)]',
    danger: 'bg-rose-950/70 text-rose-300 border-rose-500/30 shadow-[0_0_12px_-3px_rgba(244,63,94,0.2)]',
    info: 'bg-blue-950/70 text-blue-300 border-blue-500/30 shadow-[0_0_12px_-3px_rgba(59,130,246,0.2)]',
    purple: 'bg-purple-950/70 text-purple-300 border-purple-500/30 shadow-[0_0_12px_-3px_rgba(168,85,247,0.2)]',
    cyan: 'bg-cyan-950/70 text-cyan-300 border-cyan-500/30 shadow-[0_0_12px_-3px_rgba(6,182,212,0.25)]',
  };

  const dotColors = {
    default: 'bg-slate-400',
    success: 'bg-emerald-400 animate-pulse',
    warning: 'bg-amber-400',
    danger: 'bg-rose-400',
    info: 'bg-blue-400',
    purple: 'bg-purple-400',
    cyan: 'bg-cyan-400 animate-pulse',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[11px] tracking-wide',
    md: 'px-2.5 py-1 text-xs tracking-normal',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border backdrop-blur-sm transition-colors ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
