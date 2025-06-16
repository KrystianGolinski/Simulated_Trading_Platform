import { useState, lazy, Suspense } from 'react';

const SimulationSetup = lazy(() => import('./components/SimulationSetup').then(module => ({ default: module.SimulationSetup })));
const SimulationProgress = lazy(() => import('./components/SimulationProgress').then(module => ({ default: module.SimulationProgress })));
const SimulationResults = lazy(() => import('./components/SimulationResults').then(module => ({ default: module.SimulationResults })));
const Dashboard = lazy(() => import('./components/Dashboard').then(module => ({ default: module.Dashboard })));

type AppState = 'setup' | 'progress' | 'results' | 'dashboard';

function App() {
  const [currentView, setCurrentView] = useState<AppState>('setup');
  const [simulationProgress] = useState({
    isRunning: false,
    progress: 0,
    currentStep: 'Initializing...'
  });

  // Mock simulation results for development
  const mockResults = {
    simulationId: 'sim_123',
    startingCapital: 10000,
    finalPortfolioValue: 12500,
    totalReturnPercentage: 25.0,
    totalTrades: 45,
    winningTrades: 28,
    losingTrades: 17,
    equityCurve: [
      { date: '2023-01-01', value: 10000 },
      { date: '2023-03-01', value: 10500 },
      { date: '2023-06-01', value: 11200 },
      { date: '2023-09-01', value: 12100 },
      { date: '2023-12-31', value: 12500 }
    ],
    config: {
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      selectedStocks: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
      shortMAPeriod: 20,
      longMAPeriod: 50
    }
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'setup':
        return <SimulationSetup />;
      case 'progress':
        return (
          <SimulationProgress
            isRunning={simulationProgress.isRunning}
            progress={simulationProgress.progress}
            currentStep={simulationProgress.currentStep}
          />
        );
      case 'results':
        return <SimulationResults results={mockResults} />;
      case 'dashboard':
        return <Dashboard />;
      default:
        return <SimulationSetup />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Fixed Navigation Bar */}
      <nav className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-gray-900">Trading Platform</h1>
            <div className="flex space-x-6">
              <button
                onClick={() => setCurrentView('setup')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'setup'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                New Simulation
              </button>
              <button
                onClick={() => setCurrentView('results')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'results'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                Results (Demo)
              </button>
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
