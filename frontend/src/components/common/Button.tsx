import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const variantStyles = {
    primary:
      'bg-gradient-to-r from-cyan-500 via-sky-500 to-blue-600 hover:from-cyan-400 hover:via-sky-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 border border-cyan-400/30 hover:shadow-cyan-500/35',
    secondary:
      'bg-slate-800/90 hover:bg-slate-750 text-slate-200 border border-slate-700/80 hover:border-slate-600 shadow-sm',
    success:
      'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-400/30 shadow-lg shadow-emerald-950/40',
    danger:
      'bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white border border-rose-400/30 shadow-lg shadow-rose-950/40',
    outline:
      'bg-slate-900/40 hover:bg-slate-800/80 text-slate-200 border border-slate-750 hover:border-cyan-500/50 hover:text-cyan-300',
    ghost:
      'bg-transparent hover:bg-slate-800/60 text-slate-400 hover:text-slate-100 border border-transparent',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs font-medium rounded-lg',
    md: 'px-4 py-2 text-sm font-medium rounded-xl',
    lg: 'px-5 py-2.5 text-base font-semibold rounded-xl',
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 select-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? <Loader2 className="w-4 h-4 animate-spin text-current" /> : leftIcon}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};
