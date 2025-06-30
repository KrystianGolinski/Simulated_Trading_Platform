import { useState, useEffect } from 'react';
import { apiService, StockData } from '../services/api';
import { PaginationInfo } from '../types/pagination';

export const useStockData = (
  symbol: string,
  startDate: string,
  endDate: string,
  timeframe: 'daily' = 'daily',
  page: number = 1,
  pageSize: number = 1000
) => {
  const [data, setData] = useState<StockData[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol || !startDate || !endDate) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiService.getStockData(
          symbol, 
          startDate, 
          endDate, 
          timeframe,
          { page, page_size: pageSize }
        );
        setData(response.data);
        setPagination(response.pagination);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol, startDate, endDate, timeframe, page, pageSize]);

  return { data, pagination, loading, error };
};

// Hook for available stocks with pagination
export const useStocks = (page: number = 1, pageSize: number = 1000) => {
  const [stocks, setStocks] = useState<string[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await apiService.getStocks({ page, page_size: pageSize });
        setStocks(response.data);
        setPagination(response.pagination);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stocks');
      } finally {
        setLoading(false);
      }
    };

    fetchStocks();
  }, [page, pageSize]);

  return { stocks, pagination, loading, error };
};