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
      {/* Header */}
      <header style={{ backgroundColor: 'white', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0, zIndex: 10, padding: '12px 0' }}>
        <div style={{ width: '100%', padding: '0 24px' }}>
          {/* Title */}
          <div style={{ display: 'flex', justifyContent: 'center', width: '100%', marginBottom: '4px' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#111827' }}>Krystian's Trading Platform</h1>
          </div>
          
          {/* Simulation Error Indicator */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '4px' }}>
            {simulation.error && (
              <div className="flex items-center space-x-2 text-sm text-red-600">
                <span>Error</span>
              </div>
            )}
          </div>
          
          {/* Nav Buttons */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '24px' }}>
            <button
              onClick={handleResetSimulation}
              disabled={simulation.isLoading}
              style={{
                padding: '12px 24px',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: '500',
                border: 'none',
                cursor: simulation.isLoading ? 'not-allowed' : 'pointer',
                backgroundColor: currentView === 'setup' ? '#2563eb' : 'transparent',
                color: currentView === 'setup' ? 'white' : '#374151',
                opacity: simulation.isLoading ? 0.5 : 1
              }}
            >
              New Simulation
            </button>
            <button
              onClick={() => setCurrentView('dashboard')}
              style={{
                padding: '12px 24px',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: '500',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: currentView === 'dashboard' ? '#2563eb' : 'transparent',
                color: currentView === 'dashboard' ? 'white' : '#374151'
              }}
            >
              Data Dashboard
            </button>
            {simulation.currentSimulation && (
              <button
                onClick={() => setCurrentView('results')}
                style={{
                  padding: '12px 24px',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: '500',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: currentView === 'results' ? '#2563eb' : 'transparent',
                  color: currentView === 'results' ? 'white' : '#374151'
                }}
              >
                Results
              </button>
            )}
          </div>
        </div>
      </header>

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
