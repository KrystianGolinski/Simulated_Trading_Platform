import React from 'react';

interface AlertProps {
  type: 'error' | 'warning' | 'success' | 'info';
  title?: string;
  children: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}

const alertStyles = {
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  success: 'bg-green-50 border-green-200 text-green-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800'
};

export const Alert: React.FC<AlertProps> = ({ 
  type, 
  title, 
  children, 
  onDismiss, 
  className = '' 
}) => {
  return (
    <div className={`border rounded-md p-4 ${alertStyles[type]} ${className}`}>
      <div className="flex">
        <div className="flex-1">
          {title && (
            <h3 className="text-sm font-medium mb-1">{title}</h3>
          )}
          <div className="text-sm">{children}</div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};