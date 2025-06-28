import React from 'react';
import { Spinner } from './Spinner';

interface LoadingWrapperProps {
  isLoading: boolean;
  children: React.ReactNode;
  loadingText?: string;
  spinnerSize?: 'sm' | 'md' | 'lg';
  overlay?: boolean;
  minHeight?: string;
  className?: string;
}

export const LoadingWrapper: React.FC<LoadingWrapperProps> = ({
  isLoading,
  children,
  loadingText = 'Loading...',
  spinnerSize = 'md',
  overlay = false,
  minHeight = '100px',
  className = ''
}) => {
  const renderLoadingSpinner = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        minHeight,
        ...(overlay && {
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          zIndex: 10
        })
      }}
    >
      <Spinner size={spinnerSize} />
      {loadingText && (
        <span style={{ 
          fontSize: '14px', 
          color: '#6b7280',
          fontWeight: '500'
        }}>
          {loadingText}
        </span>
      )}
    </div>
  );

  if (isLoading && !overlay) {
    return (
      <div className={className}>
        {renderLoadingSpinner()}
      </div>
    );
  }

  return (
    <div className={className} style={{ position: overlay ? 'relative' : 'static' }}>
      {children}
      {isLoading && overlay && renderLoadingSpinner()}
    </div>
  );
};