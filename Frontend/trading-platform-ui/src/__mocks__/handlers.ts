import { rest, RestRequest, ResponseComposition, RestContext } from 'msw';
import { 
  StockData, 
  HealthData, 
  SimulationResponse, 
  SimulationStatusResponse,
  ValidationResult,
  SimulationResults 
} from '../services/api';

const API_BASE_URL = 'http://localhost:8000';

// Mock data
const mockStockData: StockData[] = [
  {
    time: '2023-01-01',
    symbol: 'AAPL',
    open: 150.0,
    high: 155.0,
    low: 148.0,
    close: 153.0,
    volume: 1000000
  },
  {
    time: '2023-01-02',
    symbol: 'AAPL',
    open: 153.0,
    high: 158.0,
    low: 152.0,
    close: 157.0,
    volume: 1100000
  }
];

const mockHealthData: HealthData = {
  status: 'healthy',
  database_connected: true,
  stocks_count: 50,
  daily_records_count: 10000,
  minute_records_count: 500000
};

const mockStocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'];

const mockValidationResult: ValidationResult = {
  is_valid: true,
  errors: [],
  warnings: []
};

const mockSimulationResponse: SimulationResponse = {
  simulation_id: 'test-sim-123',
  status: 'pending',
  message: 'Simulation started successfully'
};

const mockSimulationStatus: SimulationStatusResponse = {
  simulation_id: 'test-sim-123',
  status: 'running',
  progress_pct: 25.0,
  current_date: '2023-03-15',
  elapsed_time: 30.5,
  estimated_remaining: 90.0
};

const mockSimulationResults: SimulationResults = {
  simulation_id: 'test-sim-123',
  status: 'completed',
  config: {
    symbols: ['AAPL'],
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    starting_capital: 10000,
    strategy: 'ma_crossover',
    short_ma: 20,
    long_ma: 50
  },
  starting_capital: 10000,
  ending_value: 11550,
  total_return_pct: 15.5,
  performance_metrics: {
    total_return_pct: 15.5,
    sharpe_ratio: 1.34,
    max_drawdown_pct: 8.2,
    win_rate: 65.0,
    total_trades: 25,
    winning_trades: 16,
    losing_trades: 9
  },
  trades: [
    {
      date: '2023-01-15 -> 2023-01-20',
      symbol: 'AAPL',
      action: 'BUY@150.00 -> SELL@160.00 (+6.67%)',
      shares: 66,
      price: 150.0,
      total_value: 660.0
    }
  ],
  equity_curve: [
    { date: '2023-01-01', value: 10000 },
    { date: '2023-12-31', value: 11550 }
  ],
  created_at: '2023-01-01T00:00:00Z',
  started_at: '2023-01-01T00:01:00Z',
  completed_at: '2023-01-01T01:00:00Z'
};

export const handlers = [
  // Health check
  rest.get(`${API_BASE_URL}/health`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(ctx.json(mockHealthData));
  }),

  // Stock symbols list
  rest.get(`${API_BASE_URL}/stocks`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(ctx.json(mockStocks));
  }),

  // Stock data
  rest.get(`${API_BASE_URL}/stocks/:symbol/data`, (req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    const { symbol } = req.params;
    
    // Return mock data for the requested symbol
    const data = mockStockData.map(item => ({
      ...item,
      symbol: (symbol as string).toUpperCase()
    }));
    
    return res(ctx.json(data));
  }),

  // Simulation validation
  rest.post(`${API_BASE_URL}/simulation/validate`, async (req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    const config = await req.json();
    
    // Simple validation logic for testing
    if (!config || !Array.isArray((config as any).symbols) || (config as any).symbols.length === 0) {
      return res(ctx.json({
        is_valid: false,
        errors: [
          {
            field: 'symbols',
            message: 'At least one symbol is required',
            error_code: 'SYMBOLS_EMPTY'
          }
        ],
        warnings: []
      }));
    }
    
    return res(ctx.json(mockValidationResult));
  }),

  // Start simulation
  rest.post(`${API_BASE_URL}/simulation/start`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(ctx.json(mockSimulationResponse));
  }),

  // Simulation status
  rest.get(`${API_BASE_URL}/simulation/:id/status`, (req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    const { id } = req.params;
    return res(ctx.json({
      ...mockSimulationStatus,
      simulation_id: id as string
    }));
  }),

  // Simulation results
  rest.get(`${API_BASE_URL}/simulation/:id/results`, (req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    const { id } = req.params;
    return res(ctx.json({
      ...mockSimulationResults,
      simulation_id: id as string
    }));
  }),

  // Cancel simulation
  rest.delete(`${API_BASE_URL}/simulation/:id/cancel`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(ctx.json({ message: 'Simulation cancelled successfully' }));
  }),

  // List simulations
  rest.get(`${API_BASE_URL}/simulations`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(ctx.json({
      'test-sim-123': mockSimulationResults
    }));
  }),

  // Error handlers for testing error scenarios
  rest.get(`${API_BASE_URL}/stocks/ERROR/data`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(
      ctx.status(404),
      ctx.json({ message: 'Stock not found' })
    );
  }),

  rest.post(`${API_BASE_URL}/simulation/invalid`, (_req: RestRequest, res: ResponseComposition, ctx: RestContext) => {
    return res(
      ctx.status(400),
      ctx.json({ 
        message: 'Invalid simulation configuration',
        errors: ['Invalid symbols', 'Invalid date range'] 
      })
    );
  })
];