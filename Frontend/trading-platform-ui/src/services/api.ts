// API configuration and service layer
import { PaginatedResponse, PaginationRequest, PaginationUtils } from '../types/pagination';

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
  strategy: string;
  strategy_parameters: Record<string, any>;
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
  final_balance?: number;
  starting_capital?: number;
  max_drawdown?: number;
  profit_factor?: number;
  average_win?: number;
  average_loss?: number;
  annualized_return?: number;
  volatility?: number;
  signals_generated?: number;
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
      
      // Return the full response structure for the new infrastructure
      if (responseData.status === 'success' || responseData.status === 'warning') {
        return responseData as unknown as T;
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
    const response = await this.fetchWithErrorHandling<StandardResponse<any>>('/health');
    // Transform the standardized health response to the expected format
    const data = response.data;
    return {
      status: data.service ? 'healthy' : 'unhealthy',
      database_connected: data.database?.status === 'healthy',
      stocks_count: data.stocks_count || 0,
      daily_records_count: data.daily_records_count || 0,
      minute_records_count: data.minute_records_count || 0
    };
  }

  // Get list of available stock symbols with pagination
  async getStocks(paginationRequest: PaginationRequest = {}): Promise<PaginatedResponse<string>> {
    const validation = PaginationUtils.validatePaginationRequest(paginationRequest);
    const { page, page_size } = validation.sanitized;
    
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: page_size.toString()
    });
    
    return this.fetchWithErrorHandling<PaginatedResponse<string>>(`/stocks?${params}`);
  }

  // Get historical stock data with pagination
  async getStockData(
    symbol: string,
    startDate: string,
    endDate: string,
    timeframe: 'daily' = 'daily',
    paginationRequest: PaginationRequest = {}
  ): Promise<PaginatedResponse<StockData> & { symbol: string; date_range: any }> {
    const validation = PaginationUtils.validatePaginationRequest(paginationRequest);
    const { page, page_size } = validation.sanitized;
    
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      timeframe: timeframe,
      page: page.toString(),
      page_size: page_size.toString()
    });
    
    const response = await this.fetchWithErrorHandling<{
      data: any[],
      pagination: any,
      symbol: string,
      date_range: any
    }>(`/stocks/${symbol}/data?${params}`);

    // Ensure numeric conversion for price/volume data
    const processedData = response.data.map(item => ({
      time: item.time,
      symbol: item.symbol,
      open: parseFloat(item.open) || 0,
      high: parseFloat(item.high) || 0,
      low: parseFloat(item.low) || 0,
      close: parseFloat(item.close) || 0,
      volume: parseInt(item.volume) || 0,
      vwap: item.vwap ? parseFloat(item.vwap) : undefined
    }));

    return {
      data: processedData,
      pagination: response.pagination,
      symbol: response.symbol,
      date_range: response.date_range
    };
  }

  // Validate simulation configuration
  async validateSimulation(config: SimulationConfig): Promise<ValidationResult> {
    const response = await this.fetchWithErrorHandling<StandardResponse<ValidationResult>>('/simulation/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    return response.data!;
  }

  // Start a new simulation
  async startSimulation(config: SimulationConfig): Promise<SimulationResponse> {
    const response = await this.fetchWithErrorHandling<StandardResponse<SimulationResponse>>('/simulation/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    return response.data!;
  }

  // Get simulation status and progress
  async getSimulationStatus(simulationId: string): Promise<SimulationStatusResponse> {
    const response = await this.fetchWithErrorHandling<StandardResponse<SimulationStatusResponse>>(
      `/simulation/${simulationId}/status`
    );
    return response.data!;
  }

  // Get simulation results
  async getSimulationResults(simulationId: string): Promise<SimulationResults> {
    const response = await this.fetchWithErrorHandling<StandardResponse<SimulationResults>>(
      `/simulation/${simulationId}/results`
    );
    return response.data!;
  }

  // Cancel a running simulation
  async cancelSimulation(simulationId: string): Promise<{ message: string }> {
    const response = await this.fetchWithErrorHandling<StandardResponse<{ message: string }>>(
      `/simulation/${simulationId}/cancel`
    );
    return response.data!;
  }

  // List all simulations
  async listSimulations(): Promise<Record<string, SimulationResults>> {
    const response = await this.fetchWithErrorHandling<StandardResponse<Record<string, SimulationResults>>>('/simulations');
    return response.data!;
  }

  // Get date range for a specific stock
  async getStockDateRange(symbol: string): Promise<{ min_date: string; max_date: string }> {
    const response = await this.fetchWithErrorHandling<StandardResponse<{ min_date: string; max_date: string }>>(
      `/stocks/${symbol}/date-range`
    );
    return response.data!;
  }
}

export const apiService = new ApiService();