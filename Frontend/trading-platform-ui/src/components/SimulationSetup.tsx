import React, { useState } from 'react';
import { useStocks } from '../hooks/useStockData';
import { SimulationConfig, ValidationError, apiService } from '../services/api';
import { Card, FormInput, Spinner, Alert, Button, DateRangeSelector, ErrorAlert } from './common';

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
    start_date: '',
    end_date: '',
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
        <ErrorAlert
          error={error || null}
          title="Error Starting Simulation"
          onDismiss={onClearError}
          className="mb-6"
        />

        <form onSubmit={handleSubmit} className="compact-spacing">
          {/* Starting Capital */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Portfolio Settings</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', padding: '0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151', width: '140px', textAlign: 'left' }}>
                    Starting Capital ($)
                  </label>
                  <input
                    type="number"
                    min="1000"
                    max="1000000"
                    step="100"
                    value={config.starting_capital}
                    onChange={(e) => setConfig(prev => ({ ...prev, starting_capital: Number(e.target.value) }))}
                    required
                    style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '200px',
                      color: '#374151',
                      backgroundColor: '#ffffff',
                      textAlign: 'left'
                    }}
                  />
                  <Button
                    type="button"
                    onClick={() => setConfig(prev => ({ ...prev, starting_capital: 1000000 }))}
                    variant="secondary"
                    style={{ fontSize: '0.75rem', padding: '4px 8px', width: '60px', textAlign: 'center' }}
                  >
                    Max
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* Date Range */}
          <DateRangeSelector
            startDate={config.start_date}
            endDate={config.end_date}
            onStartDateChange={(date) => setConfig(prev => ({ ...prev, start_date: date }))}
            onEndDateChange={(date) => setConfig(prev => ({ ...prev, end_date: date }))}
            title="Simulation Period"
            variant="card"
            symbol={config.symbols.length > 0 ? config.symbols[0] : undefined}
            autoSetDatesOnSymbolChange={true}
          />

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
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
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
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <button
                          type="button"
                          onClick={() => {
                            setConfig(prev => ({ ...prev, symbols: [...stocks] }));
                          }}
                          style={{
                            padding: '4px 8px',
                            fontSize: '12px',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Add all
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setConfig(prev => ({ ...prev, symbols: [] }));
                          }}
                          style={{
                            padding: '4px 8px',
                            fontSize: '12px',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Clear all
                        </button>
                      </div>
                    </div>
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

          {/* Strategy Selection */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Trading Strategy</h2>
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: '500', color: '#374151' }}>Strategy Type</label>
                <select
                  value={config.strategy}
                  onChange={(e) => setConfig(prev => ({ ...prev, strategy: e.target.value as 'ma_crossover' | 'rsi' }))}
                  style={{
                    width: '100%',
                    maxWidth: '300px',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: '#ffffff'
                  }}
                >
                  <option value="ma_crossover">Moving Average Crossover</option>
                  <option value="rsi">RSI (Relative Strength Index)</option>
                </select>
              </div>

              {/* MA Crossover Parameters */}
              {config.strategy === 'ma_crossover' && (
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151', textAlign: 'center' }}>Moving Average Parameters</h3>
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
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', textAlign: 'center', whiteSpace: 'pre-line' }}>
                    Buy signal: Short MA crosses above Long MA.{'\n'}Sell signal: Short MA crosses below Long MA.
                  </p>
                </div>
              )}

              {/* RSI Parameters */}
              {config.strategy === 'rsi' && (
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151', textAlign: 'center' }}>RSI Parameters</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem' }}>
                    <FormInput
                      label="RSI Period (days)"
                      type="number"
                      min="2"
                      max="50"
                      value={config.rsi_period}
                      onChange={(e) => setConfig(prev => ({ ...prev, rsi_period: Number(e.target.value) }))}
                      required
                    />
                    <FormInput
                      label="Oversold Threshold"
                      type="number"
                      min="10"
                      max="40"
                      value={config.rsi_oversold}
                      onChange={(e) => setConfig(prev => ({ ...prev, rsi_oversold: Number(e.target.value) }))}
                      required
                    />
                    <FormInput
                      label="Overbought Threshold"
                      type="number"
                      min="60"
                      max="90"
                      value={config.rsi_overbought}
                      onChange={(e) => setConfig(prev => ({ ...prev, rsi_overbought: Number(e.target.value) }))}
                      required
                    />
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', textAlign: 'center', whiteSpace: 'pre-line' }}>
                    Buy signal: RSI crosses above oversold threshold.{'\n'}Sell signal: RSI crosses below overbought threshold.
                  </p>
                </div>
              )}
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
                    disabled={
                      config.symbols.length === 0 || 
                      (config.strategy === 'ma_crossover' && config.short_ma! >= config.long_ma!) ||
                      (config.strategy === 'rsi' && config.rsi_oversold! >= config.rsi_overbought!) ||
                      isLoading || 
                      validation.errors.length > 0
                    }
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
                
                {config.strategy === 'ma_crossover' && config.short_ma! >= config.long_ma! && (
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', textAlign: 'center' }}>Short MA period must be less than Long MA period</p>
                )}
                
                {config.strategy === 'rsi' && config.rsi_oversold! >= config.rsi_overbought! && (
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', textAlign: 'center' }}>Oversold threshold must be less than Overbought threshold</p>
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