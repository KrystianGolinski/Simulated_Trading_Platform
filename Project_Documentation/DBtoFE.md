# Frontend Database Integration Guide

## Current Architecture

```
Frontend (React) ← HTTP/REST → FastAPI Backend ← AsyncPG → TimescaleDB
    Port 3000                     Port 8000              Port 5433
```

## Available Data & API Endpoints

### Your Current API Endpoints:
- `GET /` - Welcome message
- `GET /health` - System health and database stats
- `GET /stocks` - List of available stock symbols (25 stocks + 2 indices)
- `GET /stocks/{symbol}/data` - Historical stock data with parameters:
  - `symbol`: Stock symbol (AAPL, MSFT, GOOGL, etc.)
  - `start_date`: ISO format (YYYY-MM-DD)
  - `end_date`: ISO format (YYYY-MM-DD)
  - `timeframe`: "daily" or "1min"

### Available Database Data:
- **25 Major Stocks**: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, ADBE, CRM, ORCL, IBM, INTC, CSCO, AMD, NFLX, UBER, LYFT, SNAP, TWTR, SPOT, SQ, PYPL, V, MA, JPM
- **2 Market Indices**: ^SPX (S&P 500), ^NYA (NYSE Composite)
- **Daily Data**: 10 years (2015-2025) - ~2,514 records per symbol
- **Intraday Data**: Recent 1-minute data (June 2025)

## Implementation Steps

### Step 1: Set Up API Service Layer

Create a service layer in your React app to handle API calls:

**File: `Frontend/trading-platform-ui/src/services/api.ts`**

```typescript
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
    
    return this.fetchWithErrorHandling<StockData[]>(
      `/stocks/${symbol}/data?${params}`
    );
  }
}

export const apiService = new ApiService();
```

### Step 2: Create React Hooks for Data Management

**File: `Frontend/trading-platform-ui/src/hooks/useStockData.ts`**

```typescript
import { useState, useEffect } from 'react';
import { apiService, StockData } from '../services/api';

export const useStockData = (
  symbol: string,
  startDate: string,
  endDate: string,
  timeframe: 'daily' | '1min' = 'daily'
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
```

### Step 3: Create Chart Component

**File: `Frontend/trading-platform-ui/src/components/StockChart.tsx`**

```typescript
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { StockData } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface StockChartProps {
  data: StockData[];
  symbol: string;
  loading: boolean;
  error: string | null;
}

export const StockChart: React.FC<StockChartProps> = ({ 
  data, 
  symbol, 
  loading, 
  error 
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        Error: {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No data available for the selected period
      </div>
    );
  }

  const chartData = {
    labels: data.map(d => d.time),
    datasets: [
      {
        label: `${symbol} Close Price`,
        data: data.map(d => d.close),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: false,
        tension: 0.1,
      },
      {
        label: `${symbol} Volume`,
        data: data.map(d => d.volume),
        borderColor: 'rgba(239, 68, 68, 0.5)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 1,
        yAxisID: 'y1',
        type: 'bar' as const,
      }
    ],
  };

  const options = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Stock Price & Volume`,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            day: 'MMM dd',
            month: 'MMM yyyy'
          }
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Price ($)'
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Volume'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  return (
    <div className="w-full h-96 p-4">
      <Line data={chartData} options={options} />
    </div>
  );
};
```

### Step 4: Create Main Dashboard Component

**File: `Frontend/trading-platform-ui/src/components/Dashboard.tsx`**

```typescript
import React, { useState } from 'react';
import { StockChart } from './StockChart';
import { useStockData, useStocks } from '../hooks/useStockData';

export const Dashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [startDate, setStartDate] = useState<string>('2024-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [timeframe, setTimeframe] = useState<'daily' | '1min'>('daily');

  const { stocks, loading: stocksLoading } = useStocks();
  const { data, loading, error } = useStockData(
    selectedSymbol, 
    startDate, 
    endDate, 
    timeframe
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Trading Platform Dashboard
        </h1>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stock Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stock Symbol
              </label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={stocksLoading}
              >
                {stocks.map(symbol => (
                  <option key={symbol} value={symbol}>
                    {symbol}
                  </option>
                ))}
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
                onChange={(e) => setStartDate(e.target.value)}
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
                onChange={(e) => setEndDate(e.target.value)}
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
                onChange={(e) => setTimeframe(e.target.value as 'daily' | '1min')}
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

        {/* Data Table */}
        {data.length > 0 && (
          <div className="bg-white rounded-lg shadow mt-6 p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Data</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Open
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      High
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Low
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Close
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Volume
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.slice(-10).reverse().map((row, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        {new Date(row.time).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        ${row.open.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        ${row.high.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        ${row.low.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        ${row.close.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        {row.volume.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

### Step 5: Update Your Main App Component

**File: `Frontend/trading-platform-ui/src/App.tsx`**

```typescript
import React from 'react';
import { Dashboard } from './components/Dashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;
```

### Step 6: Install Required Dependencies

Run these commands in your frontend directory:

```bash
cd Frontend/trading-platform-ui
npm install chartjs-adapter-date-fns
```

### Step 7: Environment Configuration

Create **`.env`** file in your frontend root:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Testing Your Integration

### 1. Start Your Services

```bash
# Start Docker services
cd Docker
docker-compose -f docker-compose.dev.yml up -d

# Start frontend development server
cd ../Frontend/trading-platform-ui
npm start
```

### 2. Verify Data Flow

1. **Check API health**: `http://localhost:8000/health`
2. **Check available stocks**: `http://localhost:8000/stocks`
3. **Test stock data**: `http://localhost:8000/stocks/AAPL/data?start_date=2024-01-01&end_date=2024-12-31&timeframe=daily`
4. **View frontend**: `http://localhost:3000`

## Advanced Features to Add

### 1. Real-time Data Updates

```typescript
// Add WebSocket support for real-time updates
const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    setSocket(ws);

    ws.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    return () => ws.close();
  }, [url]);

  return { socket, data };
};
```

### 2. Data Caching

```typescript
// Add React Query for caching
import { useQuery } from 'react-query';

const useStockDataCached = (symbol: string, startDate: string, endDate: string) => {
  return useQuery(
    ['stockData', symbol, startDate, endDate],
    () => apiService.getStockData(symbol, startDate, endDate),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );
};
```

### 3. Performance Optimizations

```typescript
// Add data virtualization for large datasets
import { FixedSizeList as List } from 'react-window';

// Memoize expensive calculations
const memoizedChartData = useMemo(() => {
  return processChartData(stockData);
}, [stockData]);
```

## Error Handling & Best Practices

### 1. API Error Handling

```typescript
// Implement retry logic
const fetchWithRetry = async (url: string, retries = 3): Promise<any> => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### 2. Loading States

```typescript
// Implement skeleton loading
const SkeletonChart = () => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
    <div className="h-64 bg-gray-200 rounded"></div>
  </div>
);
```

### 3. Data Validation

```typescript
// Validate API responses
const validateStockData = (data: any[]): StockData[] => {
  return data.filter(item => 
    item.time && 
    typeof item.close === 'number' && 
    item.close > 0
  );
};
```

## Security Considerations

1. **CORS Configuration**: Ensure your FastAPI CORS settings match your frontend URL
2. **Environment Variables**: Never commit API keys or sensitive data
3. **Input Validation**: Validate all user inputs (dates, symbols)
4. **Rate Limiting**: Implement API rate limiting to prevent abuse

## Performance Monitoring

```typescript
// Add performance monitoring
const usePerformanceMonitor = () => {
  useEffect(() => {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log(`${entry.name}: ${entry.duration}ms`);
      }
    });
    
    observer.observe({ entryTypes: ['measure'] });
    
    return () => observer.disconnect();
  }, []);
};
```

## Next Steps

1. **Implement the components above**
2. **Test with different stock symbols and date ranges**
3. **Add more chart types** (candlestick, volume, technical indicators)
4. **Implement portfolio tracking**
5. **Add backtesting functionality**
6. **Create responsive design for mobile**
