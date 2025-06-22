import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const variantClasses = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-600 text-white hover:bg-gray-700',
  success: 'bg-green-600 text-white hover:bg-green-700',
  danger: 'bg-red-600 text-white hover:bg-red-700'
};

const sizeClasses = {
  sm: 'px-4 py-1 text-sm',
  md: 'px-6 py-2',
  lg: 'px-8 py-3 text-lg'
};

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md', 
  loading = false,
  disabled,
  children, 
  className = '', 
  ...props 
}) => {
  return (
    <button
      className={`rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <div className="flex items-center justify-center">
          <div className={`animate-spin rounded-full border-b-2 border-white mr-2 ${size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'}`} />
          Loading...
        </div>
      ) : (
        children
      )}
    </button>
  );
};