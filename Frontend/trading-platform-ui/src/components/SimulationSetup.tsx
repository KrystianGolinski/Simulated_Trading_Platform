import React, { useState } from 'react';
import { useStocks } from '../hooks/useStockData';

interface SimulationConfig {
  startingCapital: number;
  startDate: string;
  endDate: string;
  selectedStocks: string[];
  shortMAPeriod: number;
  longMAPeriod: number;
}

export const SimulationSetup: React.FC = () => {
  const [config, setConfig] = useState<SimulationConfig>({
    startingCapital: 10000,
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    selectedStocks: [],
    shortMAPeriod: 20,
    longMAPeriod: 50
  });

  const { stocks, loading: stocksLoading } = useStocks();

  const handleStockToggle = (symbol: string) => {
    setConfig(prev => ({
      ...prev,
      selectedStocks: prev.selectedStocks.includes(symbol)
        ? prev.selectedStocks.filter(s => s !== symbol)
        : [...prev.selectedStocks, symbol]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Simulation Config:', config);
    // TODO: Connect to FastAPI simulation endpoint
    alert('Simulation will be implemented in next phase!');
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Trading Simulation Setup
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Starting Capital */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Portfolio Settings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Starting Capital ($)
                </label>
                <input
                  type="number"
                  min="1000"
                  max="1000000"
                  step="100"
                  value={config.startingCapital}
                  onChange={(e) => setConfig(prev => ({ ...prev, startingCapital: Number(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Date Range */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Simulation Period</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={config.startDate}
                  onChange={(e) => setConfig(prev => ({ ...prev, startDate: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="2015-06-17"
                  max="2025-06-13"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={config.endDate}
                  onChange={(e) => setConfig(prev => ({ ...prev, endDate: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="2015-06-17"
                  max="2025-06-13"
                  required
                />
              </div>
            </div>
          </div>

          {/* Stock Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Stock Selection</h2>
            <p className="text-sm text-gray-600 mb-4">
              Select stocks to include in your simulation ({config.selectedStocks.length} selected)
            </p>
            {stocksLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 max-h-60 overflow-y-auto">
                {stocks.map(symbol => (
                  <label key={symbol} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                    <input
                      type="checkbox"
                      checked={config.selectedStocks.includes(symbol)}
                      onChange={() => handleStockToggle(symbol)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium">{symbol}</span>
                  </label>
                ))}
              </div>
            )}
            {config.selectedStocks.length === 0 && (
              <p className="text-red-500 text-sm mt-2">Please select at least one stock</p>
            )}
          </div>

          {/* Strategy Parameters */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Moving Average Crossover Strategy</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Short MA Period (days)
                </label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  value={config.shortMAPeriod}
                  onChange={(e) => setConfig(prev => ({ ...prev, shortMAPeriod: Number(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Long MA Period (days)
                </label>
                <input
                  type="number"
                  min="20"
                  max="200"
                  value={config.longMAPeriod}
                  onChange={(e) => setConfig(prev => ({ ...prev, longMAPeriod: Number(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Buy signal: Short MA crosses above Long MA. Sell signal: Short MA crosses below Long MA.
            </p>
          </div>

          {/* Submit Button */}
          <div className="bg-white rounded-lg shadow p-6">
            <button
              type="submit"
              disabled={config.selectedStocks.length === 0 || config.shortMAPeriod >= config.longMAPeriod}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
            >
              Start Simulation
            </button>
            {config.shortMAPeriod >= config.longMAPeriod && (
              <p className="text-red-500 text-sm mt-2">Short MA period must be less than Long MA period</p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};