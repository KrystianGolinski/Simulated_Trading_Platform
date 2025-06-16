// API configuration and service layer
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface StockData {
  time: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number; // Only available for 1min data
}

export interface HealthData {
  status: string;
  database_connected: boolean;
  stocks_count: number;
  daily_records_count: number;
  minute_records_count: number;
}

class ApiService {
  private async fetchWithErrorHandling<T>(url: string): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Get system health and database statistics
  async getHealth(): Promise<HealthData> {
    return this.fetchWithErrorHandling<HealthData>('/health');
  }

  // Get list of available stock symbols
  async getStocks(): Promise<string[]> {
    return this.fetchWithErrorHandling<string[]>('/stocks');
  }

  // Get historical stock data
  async getStockData(
    symbol: string,
    startDate: string,
    endDate: string,
    timeframe: 'daily' | '1min' = 'daily'
  ): Promise<StockData[]> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      timeframe: timeframe
    });
    
    const rawData = await this.fetchWithErrorHandling<any[]>(
      `/stocks/${symbol}/data?${params}`
    );

    // Ensure numeric conversion for price/volume data
    return rawData.map(item => ({
      time: item.time,
      symbol: item.symbol,
      open: parseFloat(item.open) || 0,
      high: parseFloat(item.high) || 0,
      low: parseFloat(item.low) || 0,
      close: parseFloat(item.close) || 0,
      volume: parseInt(item.volume) || 0,
      vwap: item.vwap ? parseFloat(item.vwap) : undefined
    }));
  }
}

export const apiService = new ApiService();