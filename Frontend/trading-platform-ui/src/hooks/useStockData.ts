import { useState, useEffect } from 'react';
import { apiService, StockData } from '../services/api';

export const useStockData = (
  symbol: string,
  startDate: string,
  endDate: string,
  timeframe: 'daily' = 'daily'
) => {
  const [data, setData] = useState<StockData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol || !startDate || !endDate) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const stockData = await apiService.getStockData(
          symbol, 
          startDate, 
          endDate, 
          timeframe
        );
        setData(stockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol, startDate, endDate, timeframe]);

  return { data, loading, error };
};

// Hook for available stocks
export const useStocks = () => {
  const [stocks, setStocks] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const stockList = await apiService.getStocks();
        setStocks(stockList);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stocks');
      } finally {
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  return { stocks, loading, error };
};