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
    <div style={{ padding: '12px' }}>
      <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
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
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Portfolio Settings</h2>
            <Card>
              <div style={{ display: 'flex', justifyContent: 'center' }}>
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
          </div>

          {/* Date Range */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Simulation Period</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
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
          </div>

          {/* Stock Selection */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Stock Selection</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <p style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                  Select stocks to include in your simulation ({config.symbols.length} selected)
                </p>
                {stocksLoading ? (
                  <Spinner size="md" />
                ) : (
                  <div>
                    <select
                      multiple
                      value={config.symbols}
                      onChange={(e) => {
                        const selectedValues = Array.from(e.target.selectedOptions, option => option.value);
                        setConfig(prev => ({ ...prev, symbols: selectedValues }));
                      }}
                      style={{
                        width: 'auto',
                        minWidth: '120px',
                        height: '80px',
                        padding: '6px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '13px'
                      }}
                    >
                      {stocks.map(symbol => (
                        <option key={symbol} value={symbol}>
                          {symbol}
                        </option>
                      ))}
                    </select>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem', textAlign: 'center' }}>
                      Hold Ctrl/Cmd to select multiple stocks
                    </p>
                  </div>
                )}
                {config.symbols.length === 0 && (
                  <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '0.25rem' }}>Please select at least one stock</p>
                )}
              </div>
            </Card>
          </div>

          {/* Strategy Parameters */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Moving Average Crossover Strategy</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem' }}>
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
              <p style={{ fontSize: '0.75rem', color: '#6b7280', textAlign: 'center' }}>
                Buy signal: Short MA crosses above Long MA. Sell signal: Short MA crosses below Long MA.
              </p>
            </Card>
          </div>

          {/* Validate Button */}
          <div style={{ marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Simulation Controls</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <Button
                    type="button"
                    onClick={validateConfiguration}
                    disabled={config.symbols.length === 0 || validation.isValidating}
                    variant="secondary"
                    className="text-sm py-2 px-4"
                  >
                    {validation.isValidating ? (
                      <>
                        <Spinner size="sm" className="mr-2" />
                        Validating...
                      </>
                    ) : (
                      'Validate Configuration'
                    )}
                  </Button>
                  
                  <Button
                    type="submit"
                    disabled={config.symbols.length === 0 || config.short_ma! >= config.long_ma! || isLoading || validation.errors.length > 0}
                    variant="primary"
                    className="py-2 font-semibold text-sm px-4"
                  >
                    {isLoading ? (
                      <>
                        <Spinner size="sm" className="mr-2" />
                        Starting...
                      </>
                    ) : (
                      'Start Simulation'
                    )}
                  </Button>
                </div>
                
                {config.short_ma! >= config.long_ma! && (
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', textAlign: 'center' }}>Short MA period must be less than Long MA period</p>
                )}
                
                {validation.errors.length > 0 && (
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', textAlign: 'center' }}>Please fix configuration errors before starting simulation</p>
                )}
                
                {validation.warnings.length > 0 && validation.errors.length === 0 && (
                  <p style={{ color: '#d97706', fontSize: '0.875rem', textAlign: 'center' }}>Configuration has warnings but can still be run</p>
                )}
              </div>
            </Card>
          </div>
        </form>
      </div>
    </div>
  );
};