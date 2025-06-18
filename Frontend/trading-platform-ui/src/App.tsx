import { useState, lazy, Suspense, useEffect } from 'react';
import { useSimulation } from './hooks/useSimulation';
import { SimulationConfig } from './services/api';

const SimulationSetup = lazy(() => import('./components/SimulationSetup').then(module => ({ default: module.SimulationSetup })));
const SimulationProgress = lazy(() => import('./components/SimulationProgress').then(module => ({ default: module.SimulationProgress })));
const SimulationResults = lazy(() => import('./components/SimulationResults').then(module => ({ default: module.SimulationResults })));
const Dashboard = lazy(() => import('./components/Dashboard').then(module => ({ default: module.Dashboard })));

type AppState = 'setup' | 'progress' | 'results' | 'dashboard';

function App() {
  const [currentView, setCurrentView] = useState<AppState>('setup');
  const simulation = useSimulation();

  // Auto-navigate based on simulation state
  useEffect(() => {
    if (simulation.isLoading && currentView !== 'progress') {
      setCurrentView('progress');
    } else if (simulation.currentSimulation?.status === 'completed' && currentView !== 'results') {
      setCurrentView('results');
    } else if (simulation.error && currentView === 'progress') {
      setCurrentView('setup');
    }
  }, [simulation.isLoading, simulation.currentSimulation, simulation.error, currentView]);

  const handleStartSimulation = async (config: SimulationConfig) => {
    await simulation.startSimulation(config);
  };

  const handleResetSimulation = () => {
    simulation.reset();
    setCurrentView('setup');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'setup':
        return (
          <SimulationSetup 
            onStartSimulation={handleStartSimulation}
            isLoading={simulation.isLoading}
            error={simulation.error}
            onClearError={simulation.clearError}
          />
        );
      case 'progress':
        return (
          <SimulationProgress
            isRunning={simulation.isLoading}
            progress={simulation.status?.progress_pct || 0}
            currentStep={simulation.status?.status === 'running' ? 'Running simulation...' : 'Initializing...'}
            simulationId={simulation.currentSimulation?.simulation_id}
            onCancel={simulation.cancelSimulation}
            estimatedRemaining={simulation.status?.estimated_remaining}
            elapsedTime={simulation.status?.elapsed_time}
          />
        );
      case 'results':
        return (
          <SimulationResults 
            results={simulation.currentSimulation} 
            onStartNew={handleResetSimulation}
          />
        );
      case 'dashboard':
        return <Dashboard />;
      default:
        return (
          <SimulationSetup 
            onStartSimulation={handleStartSimulation}
            isLoading={simulation.isLoading}
            error={simulation.error}
            onClearError={simulation.clearError}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Fixed Navigation Bar */}
      <nav className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-gray-900">Trading Platform</h1>
            <div className="flex items-center space-x-6">
              {/* Simulation Status Indicator */}
              {simulation.isLoading && (
                <div className="flex items-center space-x-2 text-sm text-orange-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                  <span>Simulation Running</span>
                </div>
              )}
              {simulation.error && (
                <div className="flex items-center space-x-2 text-sm text-red-600">
                  <span>Error</span>
                </div>
              )}
              {simulation.currentSimulation?.status === 'completed' && (
                <div className="flex items-center space-x-2 text-sm text-green-600">
                  <span>Complete</span>
                </div>
              )}
              
              {/* Navigation Buttons */}
              <button
                onClick={handleResetSimulation}
                disabled={simulation.isLoading}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'setup'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                } ${simulation.isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                New Simulation
              </button>
              {simulation.currentSimulation && (
                <button
                  onClick={() => setCurrentView('results')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentView === 'results'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  Results
                </button>
              )}
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                Data Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        <Suspense fallback={
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        }>
          {renderCurrentView()}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
