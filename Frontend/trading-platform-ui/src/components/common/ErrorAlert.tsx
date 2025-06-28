import React from 'react';
import { Alert } from './Alert';

interface ErrorAlertProps {
  error: string | Error | null;
  title?: string;
  onDismiss?: () => void;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  error,
  title,
  onDismiss,
  variant = 'error',
  className = ''
}) => {
  if (!error) {
    return null;
  }

  const errorMessage = error instanceof Error ? error.message : error;
  
  // Default titles based on variant
  const defaultTitles = {
    error: 'Error',
    warning: 'Warning', 
    info: 'Information'
  };

  const alertTitle = title || defaultTitles[variant];

  // Handle different error types and provide user-friendly messages
  const formatErrorMessage = (message: string): string => {
    if (message.includes('Network Error') || message.includes('fetch')) {
      return 'Unable to connect to the server. Please check your connection and try again.';
    }
    
    if (message.includes('timeout')) {
      return 'Request timed out. Please try again.';
    }
    
    if (message.includes('500') || message.includes('Internal Server Error')) {
      return 'A server error occurred. Please try again later.';
    }
    
    if (message.includes('400') || message.includes('Bad Request')) {
      return 'Invalid request. Please check your input and try again.';
    }
    
    if (message.includes('401') || message.includes('Unauthorized')) {
      return 'You are not authorized to perform this action.';
    }
    
    if (message.includes('404') || message.includes('Not Found')) {
      return 'The requested resource was not found.';
    }
    
    return message;
  };

  const formattedMessage = formatErrorMessage(errorMessage);

  return (
    <Alert
      type={variant}
      title={alertTitle}
      onDismiss={onDismiss}
      className={className}
    >
      {formattedMessage}
    </Alert>
  );
};