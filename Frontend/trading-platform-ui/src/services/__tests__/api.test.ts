import { apiService } from '../api';
import type { 
  SimulationConfig, 
  ValidationResult, 
  SimulationResponse,
  SimulationStatusResponse,
  SimulationResults,
  HealthData,
  StockData
} from '../api';
import { server } from '../../__mocks__/server';

beforeAll(() => server.listen());
afterAll(() => server.close());

// Mock fetch globally
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('ApiService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.REACT_APP_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('fetchWithErrorHandling', () => {
    it('handles successful responses', async () => {
      const mockData = { test: 'data' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      } as Response);

      const result = await apiService.getHealth();
      expect(result).toEqual(mockData);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health', undefined);
    });

    it('handles HTTP errors with JSON error response', async () => {
      const errorResponse = {
        message: 'Validation failed',
        error_details: [{ field: 'symbols', message: 'Required field', error_code: 'REQUIRED' }]
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorResponse,
        headers: new Headers(),
        redirected: false,
        statusText: 'Bad Request',
        type: 'basic' as ResponseType,
        url: 'http://localhost:8000/health',
        clone: () => ({} as Response),
        body: null,
        bodyUsed: false,
        arrayBuffer: async () => new ArrayBuffer(0),
        blob: async () => new Blob(),
        formData: async () => new FormData(),
        text: async () => JSON.stringify(errorResponse)
      } as Response);

      try {
        await apiService.getHealth();
        fail('Expected error to be thrown');
      } catch (error: any) {
        expect(error.message).toBe('Validation failed');
        expect(error.errorDetails).toEqual(errorResponse.error_details);
        expect(error.status).toBe(400);
      }
    });

    it('handles HTTP errors without JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Not JSON'); },
        headers: new Headers(),
        redirected: false,
        statusText: 'Internal Server Error',
        type: 'basic' as ResponseType,
        url: 'http://localhost:8000/health',
        clone: () => ({} as Response),
        body: null,
        bodyUsed: false,
        arrayBuffer: async () => new ArrayBuffer(0),
        blob: async () => new Blob(),
        formData: async () => new FormData(),
        text: async () => 'Internal Server Error'
      } as Response);

      await expect(apiService.getHealth()).rejects.toThrow('HTTP error! status: 500');
    });

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiService.getHealth()).rejects.toThrow('Network error');
    });
  });

  describe('getHealth', () => {
    it('fetches system health data', async () => {
      const healthData: HealthData = {
        status: 'healthy',
        database_connected: true,
        stocks_count: 100,
        daily_records_count: 50000,
        minute_records_count: 1000000
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => healthData,
      } as Response);

      const result = await apiService.getHealth();
      expect(result).toEqual(healthData);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health', undefined);
    });
  });

  describe('getStocks', () => {
    it('fetches available stock symbols', async () => {
      const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => symbols,
      } as Response);

      const result = await apiService.getStocks();
      expect(result).toEqual(symbols);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/stocks', undefined);
    });
  });

  describe('getStockData', () => {
    it('fetches daily stock data with default parameters', async () => {
      const rawData = [
        {
          time: '2023-01-01',
          symbol: 'AAPL',
          open: '150.00',
          high: '152.00',
          low: '149.00',
          close: '151.00',
          volume: '1000000'
        }
      ];

      const expectedData: StockData[] = [
        {
          time: '2023-01-01',
          symbol: 'AAPL',
          open: 150.00,
          high: 152.00,
          low: 149.00,
          close: 151.00,
          volume: 1000000,
          vwap: undefined
        }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => rawData,
      } as Response);

      const result = await apiService.getStockData('AAPL', '2023-01-01', '2023-01-31');
      expect(result).toEqual(expectedData);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/stocks/AAPL/data?start_date=2023-01-01&end_date=2023-01-31&timeframe=daily',
        undefined
      );
    });

    it('handles invalid numeric data gracefully', async () => {
      const rawData = [
        {
          time: '2023-01-01',
          symbol: 'AAPL',
          open: 'invalid',
          high: null,
          low: '',
          close: '151.00',
          volume: 'not_a_number'
        }
      ];

      const expectedData: StockData[] = [
        {
          time: '2023-01-01',
          symbol: 'AAPL',
          open: 0,
          high: 0,
          low: 0,
          close: 151.00,
          volume: 0,
          vwap: undefined
        }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => rawData,
      } as Response);

      const result = await apiService.getStockData('AAPL', '2023-01-01', '2023-01-31');
      expect(result).toEqual(expectedData);
    });
  });

  describe('validateSimulation', () => {
    it('validates simulation configuration successfully', async () => {
      const config: SimulationConfig = {
        symbols: ['AAPL', 'GOOGL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        starting_capital: 10000,
        strategy: 'ma_crossover',
        strategy_parameters: {
          short_ma: 20,
          long_ma: 50
        }
      };

      const validationResult: ValidationResult = {
        is_valid: true,
        errors: [],
        warnings: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => validationResult,
      } as Response);

      const result = await apiService.validateSimulation(config);
      expect(result).toEqual(validationResult);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/simulation/validate',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        }
      );
    });

    it('returns validation errors', async () => {
      const config: SimulationConfig = {
        symbols: [],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        starting_capital: 500,
        strategy: 'ma_crossover',
        strategy_parameters: {
          short_ma: 20,
          long_ma: 50
        }
      };

      const validationResult: ValidationResult = {
        is_valid: false,
        errors: [
          { field: 'symbols', message: 'At least one symbol required', error_code: 'SYMBOLS_EMPTY' },
          { field: 'starting_capital', message: 'Minimum capital is $1000', error_code: 'CAPITAL_TOO_LOW' }
        ],
        warnings: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => validationResult,
      } as Response);

      const result = await apiService.validateSimulation(config);
      expect(result).toEqual(validationResult);
    });
  });

  describe('startSimulation', () => {
    it('starts a simulation successfully', async () => {
      const config: SimulationConfig = {
        symbols: ['AAPL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        starting_capital: 10000,
        strategy: 'ma_crossover',
        strategy_parameters: {
          short_ma: 20,
          long_ma: 50
        }
      };

      const response: SimulationResponse = {
        simulation_id: 'sim_12345',
        status: 'pending',
        message: 'Simulation queued successfully'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => response,
      } as Response);

      const result = await apiService.startSimulation(config);
      expect(result).toEqual(response);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/simulation/start',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        }
      );
    });
  });

  describe('getSimulationStatus', () => {
    it('fetches simulation status', async () => {
      const statusResponse: SimulationStatusResponse = {
        simulation_id: 'sim_12345',
        status: 'running',
        progress_pct: 45.5,
        current_date: '2023-06-01',
        elapsed_time: 120,
        estimated_remaining: 150
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => statusResponse,
      } as Response);

      const result = await apiService.getSimulationStatus('sim_12345');
      expect(result).toEqual(statusResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/simulation/sim_12345/status',
        undefined
      );
    });
  });

  describe('getSimulationResults', () => {
    it('fetches simulation results', async () => {
      const results: SimulationResults = {
        simulation_id: 'sim_12345',
        status: 'completed',
        config: {
          symbols: ['AAPL'],
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          starting_capital: 10000,
          strategy: 'ma_crossover',
          strategy_parameters: {
            short_ma: 20,
            long_ma: 50
          }
        },
        starting_capital: 10000,
        ending_value: 12500,
        total_return_pct: 25.0,
        performance_metrics: {
          total_return_pct: 25.0,
          max_drawdown_pct: -5.0,
          win_rate: 65.0,
          total_trades: 100,
          winning_trades: 65,
          losing_trades: 35
        },
        equity_curve: [
          { date: '2023-01-01', value: 10000 },
          { date: '2023-12-31', value: 12500 }
        ],
        created_at: '2023-01-01T00:00:00Z'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => results,
      } as Response);

      const result = await apiService.getSimulationResults('sim_12345');
      expect(result).toEqual(results);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/simulation/sim_12345/results',
        undefined
      );
    });
  });

  describe('cancelSimulation', () => {
    it('cancels a running simulation', async () => {
      const response = { message: 'Simulation cancelled successfully' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => response,
      } as Response);

      const result = await apiService.cancelSimulation('sim_12345');
      expect(result).toEqual(response);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/simulation/sim_12345/cancel',
        undefined
      );
    });
  });

  describe('listSimulations', () => {
    it('lists all simulations', async () => {
      const simulations: Record<string, SimulationResults> = {
        'sim_1': {
          simulation_id: 'sim_1',
          status: 'completed',
          config: {
            symbols: ['AAPL'],
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            starting_capital: 10000,
            strategy: 'ma_crossover',
            strategy_parameters: {
              short_ma: 20,
              long_ma: 50
            }
          },
          created_at: '2023-01-01T00:00:00Z'
        },
        'sim_2': {
          simulation_id: 'sim_2',
          status: 'failed',
          config: {
            symbols: ['GOOGL'],
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            starting_capital: 5000,
            strategy: 'rsi',
            strategy_parameters: {
              rsi_period: 14,
              rsi_oversold: 30,
              rsi_overbought: 70
            }
          },
          created_at: '2023-01-02T00:00:00Z',
          error_message: 'Insufficient data'
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => simulations,
      } as Response);

      const result = await apiService.listSimulations();
      expect(result).toEqual(simulations);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/simulations', undefined);
    });
  });

  describe('API Base URL configuration', () => {
    it('falls back to localhost when no environment variable', async () => {
      delete process.env.REACT_APP_API_URL;
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'ok' }),
      } as Response);

      await apiService.getHealth();
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health', undefined);
    });
  });

  describe('Error handling edge cases', () => {
    it('preserves error details in thrown errors', async () => {
      const errorResponse = {
        message: 'Validation failed',
        error_details: [{ field: 'symbols', message: 'Required', error_code: 'REQUIRED' }],
        errors: ['General error']
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorResponse,
        headers: new Headers(),
        redirected: false,
        statusText: 'Bad Request',
        type: 'basic' as ResponseType,
        url: 'http://localhost:8000/health',
        clone: () => ({} as Response),
        body: null,
        bodyUsed: false,
        arrayBuffer: async () => new ArrayBuffer(0),
        blob: async () => new Blob(),
        formData: async () => new FormData(),
        text: async () => JSON.stringify(errorResponse)
      } as Response);

      try {
        await apiService.getHealth();
        fail('Expected error to be thrown');
      } catch (error: any) {
        expect(error.message).toBe('Validation failed');
        expect(error.errorDetails).toEqual(errorResponse.error_details);
        expect(error.errors).toEqual(errorResponse.errors);
        expect(error.status).toBe(400);
      }
    });

    it('handles missing error message in response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({}),
      } as Response);

      await expect(apiService.getHealth()).rejects.toThrow('HTTP error! status: 404');
    });
  });
});