import React from 'react';

interface SimulationProgressProps {
  isRunning: boolean;
  progress: number;
  currentStep: string;
  simulationId?: string;
  onCancel?: () => Promise<void>;
  estimatedRemaining?: number;
  elapsedTime?: number;
}

export const SimulationProgress: React.FC<SimulationProgressProps> = ({
  isRunning,
  progress,
  currentStep,
  simulationId,
  onCancel,
  estimatedRemaining,
  elapsedTime
}) => {
  if (!isRunning) return null;

  return (
    <div style={{ padding: '12px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
          Simulation In Progress
        </h1>
        
        <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
          {/* Progress Bar */}
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{ 
                  width: `${progress}%`, 
                  height: '100%', 
                  backgroundColor: '#3b82f6', 
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }}
              ></div>
            </div>
          </div>

          {/* Current Step */}
          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ fontSize: '1rem', color: '#374151', marginBottom: '0.5rem' }}>Current Step:</p>
            <p style={{ fontSize: '1.125rem', fontWeight: '600', color: '#2563eb' }}>{currentStep}</p>
          </div>

          {/* Time Information */}
          <div style={{ marginBottom: '1.5rem' }}>
            {elapsedTime && (
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Elapsed time: {Math.floor(elapsedTime)} seconds
              </p>
            )}
            {estimatedRemaining && (
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Estimated time remaining: {Math.ceil(estimatedRemaining)} seconds
              </p>
            )}
            {simulationId && (
              <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                Simulation ID: {simulationId.slice(0, 8)}...
              </p>
            )}
          </div>

          {/* Loading Animation and Cancel Button */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid #e5e7eb',
              borderTop: '4px solid #3b82f6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
            {onCancel && (
              <button
                onClick={onCancel}
                style={{
                  backgroundColor: '#dc2626',
                  color: 'white',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  border: 'none',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Cancel Simulation
              </button>
            )}
          </div>

          {/* Steps Indicator */}
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#374151' }}>Simulation Steps:</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {[
                'Initializing simulation engine',
                'Loading historical data',
                'Processing trading signals',
                'Executing trades',
                'Calculating performance metrics',
                'Generating results'
              ].map((step, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: currentStep === step 
                      ? '#2563eb' 
                      : progress > (index + 1) * 16.67 
                        ? '#10b981' 
                        : '#d1d5db',
                    animation: currentStep === step ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
                  }}></div>
                  <span style={{
                    fontSize: '0.875rem',
                    color: currentStep === step 
                      ? '#2563eb' 
                      : progress > (index + 1) * 16.67 
                        ? '#059669' 
                        : '#6b7280',
                    fontWeight: currentStep === step ? '600' : '500'
                  }}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};