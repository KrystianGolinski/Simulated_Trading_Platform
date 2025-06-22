import React, { useState, useMemo, useCallback } from 'react';
import { StockChart } from './StockChart';
import { useStockData, useStocks } from '../hooks/useStockData';
import { useDebounce } from '../hooks/useDebounce';

export const Dashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [startDate, setStartDate] = useState<string>('2024-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [timeframe, setTimeframe] = useState<'daily' | '1min'>('daily');

  const debouncedSymbol = useDebounce(selectedSymbol, 500);
  const debouncedStartDate = useDebounce(startDate, 800);
  const debouncedEndDate = useDebounce(endDate, 800);
  const debouncedTimeframe = useDebounce(timeframe, 300);

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

  const handleTimeframeChange = useCallback((tf: 'daily' | '1min') => {
    setTimeframe(tf);
  }, []);

  const stockOptions = useMemo(() => 
    stocks.map(symbol => (
      <option key={symbol} value={symbol}>
        {symbol}
      </option>
    )), [stocks]
  );

  return (
    <div className="container-lg">
      <h1 className="page-title">
        Trading Platform Dashboard
      </h1>

      {/* Controls */}
      <div className="card-md mb-4">
        <div className="grid-responsive-4">
          {/* Stock Selection */}
          <div>
            <label className="form-label">
              Stock Symbol
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => handleSymbolChange(e.target.value)}
              className="form-input"
              disabled={stocksLoading}
            >
              {stockOptions}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="form-label">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => handleStartDateChange(e.target.value)}
              className="form-input"
              min="2015-06-17"
              max="2025-06-13"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="form-label">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => handleEndDateChange(e.target.value)}
              className="form-input"
              min="2015-06-17"
              max="2025-06-13"
            />
          </div>

          {/* Timeframe */}
          <div>
            <label className="form-label">
              Timeframe
            </label>
            <select
              value={timeframe}
              onChange={(e) => handleTimeframeChange(e.target.value as 'daily' | '1min')}
              className="form-input"
            >
              <option value="daily">Daily</option>
              <option value="1min">1 Minute</option>
            </select>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="card-base mb-4">
        <div className="chart-container">
          <StockChart
            data={data}
            symbol={selectedSymbol}
            loading={loading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
};