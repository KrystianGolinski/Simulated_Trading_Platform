import React, { useState } from 'react';
import { useStocks } from '../hooks/useStockData';
import { SimulationConfig, ValidationError, apiService } from '../services/api';

interface SimulationSetupProps {
  onStartSimulation: (config: SimulationConfig) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

interface ValidationDisplay {
  errors: ValidationError[];
  warnings: string[];
  isValidating: boolean;
}

export const SimulationSetup: React.FC<SimulationSetupProps> = ({
  onStartSimulation,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [config, setConfig] = useState<SimulationConfig>({
    symbols: [],
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    starting_capital: 10000,
    strategy: 'ma_crossover',
    short_ma: 20,
    long_ma: 50,
    rsi_period: 14,
    rsi_oversold: 30,
    rsi_overbought: 70
  });

  const [validation, setValidation] = useState<ValidationDisplay>({
    errors: [],
    warnings: [],
    isValidating: false
  });

  const { stocks, loading: stocksLoading } = useStocks();

  const handleStockToggle = (symbol: string) => {
    setConfig(prev => ({
      ...prev,
      symbols: prev.symbols.includes(symbol)
        ? prev.symbols.filter(s => s !== symbol)
        : [...prev.symbols, symbol]
    }));
  };

  const validateConfiguration = async () => {
    setValidation(prev => ({ ...prev, isValidating: true }));
    
    try {
      const result = await apiService.validateSimulation(config);
      setValidation({
        errors: result.errors,
        warnings: result.warnings,
        isValidating: false
      });
      return result.is_valid;
    } catch (err) {
      console.error('Validation error:', err);
      setValidation({
        errors: [{ field: 'general', message: 'Validation service unavailable', error_code: 'SERVICE_ERROR' }],
        warnings: [],
        isValidating: false
      });
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (onClearError) {
      onClearError();
    }
    
    // Clear previous validation
    setValidation({ errors: [], warnings: [], isValidating: false });
    
    // Validate before starting simulation
    const isValid = await validateConfiguration();
    if (!isValid) {
      return; // Don't start simulation if validation fails
    }
    
    try {
      await onStartSimulation(config);
    } catch (err) {
      console.error('Error starting simulation:', err);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Trading Simulation Setup
        </h1>

        {/* Validation Errors */}
        {validation.errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Configuration Errors</h3>
                <div className="mt-2 space-y-1">
                  {validation.errors.map((error, index) => (
                    <div key={index} className="text-sm text-red-700">
                      <strong>{error.field}:</strong> {error.message}
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={() => setValidation(prev => ({ ...prev, errors: [] }))}
                    className="bg-red-100 px-2 py-1 text-xs rounded text-red-800 hover:bg-red-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Validation Warnings */}
        {validation.warnings.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Configuration Warnings</h3>
                <div className="mt-2 space-y-1">
                  {validation.warnings.map((warning, index) => (
                    <div key={index} className="text-sm text-yellow-700">
                      {warning}
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={() => setValidation(prev => ({ ...prev, warnings: [] }))}
                    className="bg-yellow-100 px-2 py-1 text-xs rounded text-yellow-800 hover:bg-yellow-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* General Errors */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Starting Simulation</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={onClearError}
                    className="bg-red-100 px-2 py-1 text-xs rounded text-red-800 hover:bg-red-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

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
                  value={config.starting_capital}
                  onChange={(e) => setConfig(prev => ({ ...prev, starting_capital: Number(e.target.value) }))}
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
                  value={config.start_date}
                  onChange={(e) => setConfig(prev => ({ ...prev, start_date: e.target.value }))}
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
                  value={config.end_date}
                  onChange={(e) => setConfig(prev => ({ ...prev, end_date: e.target.value }))}
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
              Select stocks to include in your simulation ({config.symbols.length} selected)
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
                      checked={config.symbols.includes(symbol)}
                      onChange={() => handleStockToggle(symbol)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium">{symbol}</span>
                  </label>
                ))}
              </div>
            )}
            {config.symbols.length === 0 && (
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
                  value={config.short_ma}
                  onChange={(e) => setConfig(prev => ({ ...prev, short_ma: Number(e.target.value) }))}
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
                  value={config.long_ma}
                  onChange={(e) => setConfig(prev => ({ ...prev, long_ma: Number(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Buy signal: Short MA crosses above Long MA. Sell signal: Short MA crosses below Long MA.
            </p>
          </div>

          {/* Validate Button */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="space-y-3">
              <button
                type="button"
                onClick={validateConfiguration}
                disabled={config.symbols.length === 0 || validation.isValidating}
                className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium flex items-center justify-center"
              >
                {validation.isValidating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Validating Configuration...
                  </>
                ) : (
                  'Validate Configuration'
                )}
              </button>
              
              <button
                type="submit"
                disabled={config.symbols.length === 0 || config.short_ma! >= config.long_ma! || isLoading || validation.errors.length > 0}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting Simulation...
                  </>
                ) : (
                  'Start Simulation'
                )}
              </button>
            </div>
            
            {config.short_ma! >= config.long_ma! && (
              <p className="text-red-500 text-sm mt-2">Short MA period must be less than Long MA period</p>
            )}
            
            {validation.errors.length > 0 && (
              <p className="text-red-500 text-sm mt-2">Please fix configuration errors before starting simulation</p>
            )}
            
            {validation.warnings.length > 0 && validation.errors.length === 0 && (
              <p className="text-yellow-600 text-sm mt-2">Configuration has warnings but can still be run</p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};