import React, { useState, useMemo, useCallback } from 'react';
import { StockChart } from './StockChart';
import { useStockData, useStocks } from '../hooks/useStockData';
import { useDebounce } from '../hooks/useDebounce';

type ChartType = 'line' | 'candlestick' | 'ohlc';

export const Dashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [startDate, setStartDate] = useState<string>('2024-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [timeframe, setTimeframe] = useState<'daily'>('daily');
  const [chartType, setChartType] = useState<ChartType>('line');
  const [showVolume, setShowVolume] = useState<boolean>(false);

  const debouncedSymbol = useDebounce(selectedSymbol, 500);
  const debouncedStartDate = useDebounce(startDate, 800);
  const debouncedEndDate = useDebounce(endDate, 800);
  const debouncedTimeframe = useDebounce(timeframe, 300);
  const debouncedChartType = useDebounce(chartType, 200);

  const { stocks, loading: stocksLoading } = useStocks();
  const { data, loading, error } = useStockData(
    debouncedSymbol, 
    debouncedStartDate, 
    debouncedEndDate, 
    debouncedTimeframe
  );

  const handleSymbolChange = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
  }, []);

  const handleStartDateChange = useCallback((date: string) => {
    setStartDate(date);
  }, []);

  const handleEndDateChange = useCallback((date: string) => {
    setEndDate(date);
  }, []);

  const handleTimeframeChange = useCallback((tf: 'daily') => {
    setTimeframe(tf);
  }, []);

  const handleChartTypeChange = useCallback((type: ChartType) => {
    setChartType(type);
  }, []);

  const stockOptions = useMemo(() => 
    stocks.map(symbol => (
      <option key={symbol} value={symbol}>
        {symbol}
      </option>
    )), [stocks]
  );

  return (
    <div style={{ padding: '12px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
          Trading Platform Dashboard
        </h1>

        {/* Controls */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Chart Settings</h2>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
              {/* Stock Selection */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  Stock Symbol
                </label>
                <select
                  value={selectedSymbol}
                  onChange={(e) => handleSymbolChange(e.target.value)}
                  disabled={stocksLoading}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    outline: 'none',
                    width: '140px'
                  }}
                >
                  {stockOptions}
                </select>
              </div>

              {/* Start Date */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => handleStartDateChange(e.target.value)}
                  min="2015-06-17"
                  max="2025-06-13"
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    outline: 'none',
                    width: '140px'
                  }}
                />
              </div>

              {/* End Date */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => handleEndDateChange(e.target.value)}
                  min="2015-06-17"
                  max="2025-06-13"
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    outline: 'none',
                    width: '140px'
                  }}
                />
              </div>

              {/* Timeframe */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  Timeframe
                </label>
                <select
                  value={timeframe}
                  onChange={(e) => handleTimeframeChange(e.target.value as 'daily')}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    outline: 'none',
                    width: '140px'
                  }}
                >
                  <option value="daily">Daily</option>
                </select>
              </div>

              {/* Chart Type */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  Chart Type
                </label>
                <select
                  value={chartType}
                  onChange={(e) => handleChartTypeChange(e.target.value as ChartType)}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    outline: 'none',
                    width: '140px'
                  }}
                >
                  <option value="line">Line Chart</option>
                  <option value="candlestick">Candlestick</option>
                  <option value="ohlc">OHLC Bars</option>
                </select>
              </div>

              {/* Show Volume */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
                  Show Volume
                </label>
                <input
                  type="checkbox"
                  checked={showVolume}
                  onChange={(e) => setShowVolume(e.target.checked)}
                  style={{
                    width: '16px',
                    height: '16px',
                    cursor: 'pointer'
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div style={{ marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Stock Chart</h2>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <StockChart
              data={data}
              symbol={selectedSymbol}
              loading={loading}
              error={error}
              chartType={debouncedChartType}
              showVolume={showVolume}
            />
          </div>
        </div>
      </div>
    </div>
  );
};