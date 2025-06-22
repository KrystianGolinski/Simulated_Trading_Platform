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
    <div className="container-sm">
        <div className="card-xl">
          <h1 className="section-title text-center">
            Simulation in Progress
          </h1>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Current Step */}
          <div className="text-center mb-6">
            <p className="text-lg text-gray-700 mb-2">Current Step:</p>
            <p className="text-xl font-semibold text-blue-600">{currentStep}</p>
          </div>

          {/* Time Information */}
          <div className="text-center mb-6 space-y-2">
            {elapsedTime && (
              <p className="text-sm text-gray-600">
                Elapsed time: {Math.floor(elapsedTime)} seconds
              </p>
            )}
            {estimatedRemaining && (
              <p className="text-sm text-gray-600">
                Estimated time remaining: {Math.ceil(estimatedRemaining)} seconds
              </p>
            )}
            {simulationId && (
              <p className="text-xs text-gray-500">
                Simulation ID: {simulationId.slice(0, 8)}...
              </p>
            )}
          </div>

          {/* Loading Animation and Cancel Button */}
          <div className="flex-col-center space-y-4">
            <div className="spinner-lg-blue"></div>
            {onCancel && (
              <button
                onClick={onCancel}
                className="btn-danger text-sm"
              >
                Cancel Simulation
              </button>
            )}
          </div>

          {/* Steps Indicator */}
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4">Simulation Steps:</h3>
            <div className="space-y-2">
              {[
                'Initializing simulation engine',
                'Loading historical data',
                'Processing trading signals',
                'Executing trades',
                'Calculating performance metrics',
                'Generating results'
              ].map((step, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${
                    currentStep === step 
                      ? 'bg-blue-600 animate-pulse' 
                      : progress > (index + 1) * 16.67 
                        ? 'bg-green-500' 
                        : 'bg-gray-300'
                  }`}></div>
                  <span className={`text-sm ${
                    currentStep === step 
                      ? 'text-blue-600 font-semibold' 
                      : progress > (index + 1) * 16.67 
                        ? 'text-green-600' 
                        : 'text-gray-500'
                  }`}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
    </div>
  );
};