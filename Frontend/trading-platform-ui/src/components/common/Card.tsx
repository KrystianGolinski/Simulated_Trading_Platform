import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  padding?: 'sm' | 'md' | 'lg';
  className?: string;
}

const paddingClasses = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8'
};

export const Card: React.FC<CardProps> = ({ 
  children, 
  title, 
  padding = 'md', 
  className = '' 
}) => {
  return (
    <div className={`bg-white rounded-lg shadow ${paddingClasses[padding]} ${className}`}>
      {title && (
        <h2 className="text-xl font-semibold mb-4">{title}</h2>
      )}
      {children}
    </div>
  );
};