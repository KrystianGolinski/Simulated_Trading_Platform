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
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Trading Platform Dashboard
        </h1>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stock Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stock Symbol
              </label>
              <select
                value={selectedSymbol}
                onChange={(e) => handleSymbolChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={stocksLoading}
              >
                {stockOptions}
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => handleStartDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="2015-06-17"
                max="2025-06-13"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => handleEndDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="2015-06-17"
                max="2025-06-13"
              />
            </div>

            {/* Timeframe */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => handleTimeframeChange(e.target.value as 'daily' | '1min')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="daily">Daily</option>
                <option value="1min">1 Minute</option>
              </select>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-lg shadow">
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