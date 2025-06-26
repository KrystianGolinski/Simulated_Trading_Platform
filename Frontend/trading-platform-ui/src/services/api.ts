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
}

export interface HealthData {
  status: string;
  database_connected: boolean;
  stocks_count: number;
  daily_records_count: number;
  minute_records_count: number;
}

export interface SimulationConfig {
  symbols: string[];
  start_date: string;
  end_date: string;
  starting_capital: number;
  strategy: 'ma_crossover' | 'rsi';
  short_ma?: number;
  long_ma?: number;
  rsi_period?: number;
  rsi_oversold?: number;
  rsi_overbought?: number;
}

export interface SimulationResponse {
  simulation_id: string;
  status: string;
  message: string;
}

export interface SimulationStatusResponse {
  simulation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress_pct?: number;
  current_date?: string;
  elapsed_time?: number;
  estimated_remaining?: number;
}

export interface TradeRecord {
  date: string;
  symbol: string;
  action: string;
  shares: number;
  price: number;
  total_value: number;
}

export interface PerformanceMetrics {
  total_return_pct: number;
  sharpe_ratio?: number;
  max_drawdown_pct: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
}

export interface ValidationError {
  field: string;
  message: string;
  error_code: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: string[];
}

export interface ApiErrorResponse {
  message: string;
  errors?: string[];
  error_details?: ValidationError[];
}

// Standardized response format
export interface StandardResponse<T> {
  status: 'success' | 'error' | 'warning';
  message: string;
  data?: T;
  errors?: Array<{
    code: string;
    message: string;
    field?: string;
    details?: any;
  }>;
  warnings?: string[];
  metadata?: any;
}

export interface SimulationResults {
  simulation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config: SimulationConfig;
  starting_capital?: number;
  ending_value?: number;
  total_return_pct?: number;
  performance_metrics?: PerformanceMetrics;
  trades?: TradeRecord[];
  equity_curve?: Array<{date: string; value: number}>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

class ApiService {
  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, options);
      const responseData: StandardResponse<T> = await response.json();
      
      if (!response.ok || responseData.status === 'error') {
        const error = new Error(responseData.message || `HTTP error! status: ${response.status}`);
        (error as any).errorDetails = responseData.errors;
        (error as any).errors = responseData.errors?.map(e => e.message);
        (error as any).status = response.status;
        throw error;
      }
      
      // For success responses, extract the data field
      if (responseData.status === 'success' || responseData.status === 'warning') {
        return responseData.data as T;
      }
      
      // Fallback for any non-standard responses
      return responseData as unknown as T;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Get system health and database statistics
  async getHealth(): Promise<HealthData> {
    const response = await this.fetchWithErrorHandling<any>('/health');
    // Transform the standardized health response to the expected format
    return {
      status: response.service ? 'healthy' : 'unhealthy',
      database_connected: response.database?.status === 'healthy',
      stocks_count: response.stocks_count || 0,
      daily_records_count: 0,
      minute_records_count: 0
    };
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
    timeframe: 'daily'
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

  // Validate simulation configuration
  async validateSimulation(config: SimulationConfig): Promise<ValidationResult> {
    return this.fetchWithErrorHandling<ValidationResult>('/simulation/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
  }

  // Start a new simulation
  async startSimulation(config: SimulationConfig): Promise<SimulationResponse> {
    return this.fetchWithErrorHandling<SimulationResponse>('/simulation/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
  }

  // Get simulation status and progress
  async getSimulationStatus(simulationId: string): Promise<SimulationStatusResponse> {
    return this.fetchWithErrorHandling<SimulationStatusResponse>(
      `/simulation/${simulationId}/status`
    );
  }

  // Get simulation results
  async getSimulationResults(simulationId: string): Promise<SimulationResults> {
    return this.fetchWithErrorHandling<SimulationResults>(
      `/simulation/${simulationId}/results`
    );
  }

  // Cancel a running simulation
  async cancelSimulation(simulationId: string): Promise<{ message: string }> {
    return this.fetchWithErrorHandling<{ message: string }>(
      `/simulation/${simulationId}/cancel`
    );
  }

  // List all simulations
  async listSimulations(): Promise<Record<string, SimulationResults>> {
    return this.fetchWithErrorHandling<Record<string, SimulationResults>>('/simulations');
  }

  // Get date range for a specific stock
  async getStockDateRange(symbol: string): Promise<{ min_date: string; max_date: string }> {
    return this.fetchWithErrorHandling<{ min_date: string; max_date: string }>(
      `/stocks/${symbol}/date-range`
    );
  }
}

export const apiService = new ApiService();