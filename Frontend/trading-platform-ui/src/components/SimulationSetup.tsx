import React, { useState } from 'react';
import { useStocks } from '../hooks/useStockData';
import { SimulationConfig, ValidationError, apiService } from '../services/api';
import { Card, FormInput, Spinner, Alert, Button } from './common';

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
    <div className="container-md">
      <h1 className="page-title">
        Trading Simulation Setup
      </h1>

        {/* Validation Errors */}
        {validation.errors.length > 0 && (
          <Alert
            type="error"
            title="Configuration Errors"
            onDismiss={() => setValidation(prev => ({ ...prev, errors: [] }))}
            className="mb-6"
          >
            <div className="space-y-1">
              {validation.errors.map((error, index) => (
                <div key={index}>
                  <strong>{error.field}:</strong> {error.message}
                </div>
              ))}
            </div>
          </Alert>
        )}

        {/* Validation Warnings */}
        {validation.warnings.length > 0 && (
          <Alert
            type="warning"
            title="Configuration Warnings"
            onDismiss={() => setValidation(prev => ({ ...prev, warnings: [] }))}
            className="mb-6"
          >
            <div className="space-y-1">
              {validation.warnings.map((warning, index) => (
                <div key={index}>{warning}</div>
              ))}
            </div>
          </Alert>
        )}

        {/* General Errors */}
        {error && (
          <Alert
            type="error"
            title="Error Starting Simulation"
            onDismiss={onClearError}
            className="mb-6"
          >
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="compact-spacing">
          {/* Starting Capital */}
          <Card title="Portfolio Settings">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <FormInput
                label="Starting Capital ($)"
                type="number"
                min="1000"
                max="1000000"
                step="100"
                value={config.starting_capital}
                onChange={(e) => setConfig(prev => ({ ...prev, starting_capital: Number(e.target.value) }))}
                required
              />
            </div>
          </Card>

          {/* Date Range */}
          <Card title="Simulation Period">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <FormInput
                label="Start Date"
                type="date"
                value={config.start_date}
                onChange={(e) => setConfig(prev => ({ ...prev, start_date: e.target.value }))}
                min="2015-06-17"
                max="2025-06-13"
                required
              />
              <FormInput
                label="End Date"
                type="date"
                value={config.end_date}
                onChange={(e) => setConfig(prev => ({ ...prev, end_date: e.target.value }))}
                min="2015-06-17"
                max="2025-06-13"
                required
              />
            </div>
          </Card>

          {/* Stock Selection */}
          <Card title="Stock Selection">
            <p className="text-sm text-gray-600 mb-2">
              Select stocks to include in your simulation ({config.symbols.length} selected)
            </p>
            {stocksLoading ? (
              <div className="flex justify-center py-2">
                <Spinner size="md" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 max-h-32 overflow-y-auto">
                {stocks.map(symbol => (
                  <label key={symbol} className="flex items-center space-x-1 cursor-pointer hover:bg-gray-50 p-1 rounded">
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
              <p className="text-red-500 text-sm mt-1">Please select at least one stock</p>
            )}
          </Card>

          {/* Strategy Parameters */}
          <Card title="Moving Average Crossover Strategy">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <FormInput
                label="Short MA Period (days)"
                type="number"
                min="5"
                max="50"
                value={config.short_ma}
                onChange={(e) => setConfig(prev => ({ ...prev, short_ma: Number(e.target.value) }))}
                required
              />
              <FormInput
                label="Long MA Period (days)"
                type="number"
                min="20"
                max="200"
                value={config.long_ma}
                onChange={(e) => setConfig(prev => ({ ...prev, long_ma: Number(e.target.value) }))}
                required
              />
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Buy signal: Short MA crosses above Long MA. Sell signal: Short MA crosses below Long MA.
            </p>
          </Card>

          {/* Validate Button */}
          <Card title="Simulation Controls">
            <div className="space-y-2">
              <Button
                type="button"
                onClick={validateConfiguration}
                disabled={config.symbols.length === 0 || validation.isValidating}
                variant="secondary"
                className="w-full text-sm py-2"
              >
                {validation.isValidating ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Validating Configuration...
                  </>
                ) : (
                  'Validate Configuration'
                )}
              </Button>
              
              <Button
                type="submit"
                disabled={config.symbols.length === 0 || config.short_ma! >= config.long_ma! || isLoading || validation.errors.length > 0}
                variant="primary"
                className="w-full py-2 font-semibold text-sm"
              >
                {isLoading ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Starting Simulation...
                  </>
                ) : (
                  'Start Simulation'
                )}
              </Button>
            </div>
            
            {config.short_ma! >= config.long_ma! && (
              <p className="text-red-500 text-sm mt-1">Short MA period must be less than Long MA period</p>
            )}
            
            {validation.errors.length > 0 && (
              <p className="text-red-500 text-sm mt-1">Please fix configuration errors before starting simulation</p>
            )}
            
            {validation.warnings.length > 0 && validation.errors.length === 0 && (
              <p className="text-yellow-600 text-sm mt-1">Configuration has warnings but can still be run</p>
            )}
          </Card>
        </form>
    </div>
  );
};