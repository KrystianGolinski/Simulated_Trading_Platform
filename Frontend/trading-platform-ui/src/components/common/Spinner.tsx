import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'white';
  className?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8', 
  lg: 'h-12 w-12'
};

const colorClasses = {
  blue: 'border-blue-500',
  white: 'border-white'
};

export const Spinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  color = 'blue', 
  className = '' 
}) => {
  return (
    <div 
      className={`animate-spin rounded-full border-b-2 ${sizeClasses[size]} ${colorClasses[color]} ${className}`}
    />
  );
};