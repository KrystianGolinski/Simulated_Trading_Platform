import { ConsolidatedSimulationService, SimulationState } from '../simulationService';
import { apiService } from '../api';
import type { 
  SimulationConfig, 
  SimulationResponse,
  SimulationResults 
} from '../api';

// Mock API service
jest.mock('../api', () => ({
  apiService: {
    validateSimulation: jest.fn(),
    startSimulation: jest.fn(),
    getSimulationStatus: jest.fn(),
    getSimulationResults: jest.fn(),
    cancelSimulation: jest.fn()
  }
}));

const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock timers
jest.useFakeTimers();

// Set timeout for long-running tests
jest.setTimeout(10000);

describe('ConsolidatedSimulationService', () => {
  let service: ConsolidatedSimulationService;
  let mockStateUpdate: jest.Mock<void, [SimulationState]>;

  const mockConfig: SimulationConfig = {
    symbols: ['AAPL', 'GOOGL'],
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    starting_capital: 10000,
    strategy: 'ma_crossover',
    short_ma: 20,
    long_ma: 50
  };

  beforeEach(() => {
    service = new ConsolidatedSimulationService();
    mockStateUpdate = jest.fn();
    jest.clearAllMocks();
  });

  afterEach(() => {
    service.cleanup();
    jest.clearAllTimers();
  });

  describe('startSimulation', () => {
    it('successfully starts simulation', async () => {
      const simulationResponse: SimulationResponse = {
        simulation_id: 'sim_12345',
        status: 'pending',
        message: 'Simulation started'
      };

      mockApiService.startSimulation.mockResolvedValue(simulationResponse);
      mockApiService.getSimulationStatus.mockResolvedValue({
        simulation_id: 'sim_12345',
        status: 'running',
        progress_pct: 0
      });

      service.subscribe(mockStateUpdate);
      await service.startSimulation(mockConfig);

      expect(mockApiService.startSimulation).toHaveBeenCalledWith(mockConfig);
      expect(mockStateUpdate).toHaveBeenCalled();
      
      // Check final state
      const finalState = service.getState();
      expect(finalState.currentSimulationId).toBe('sim_12345');
      expect(finalState.isLoading).toBe(true);
    });

    it('handles API errors during simulation start', async () => {
      mockApiService.startSimulation.mockRejectedValue(new Error('Server error'));

      service.subscribe(mockStateUpdate);
      await service.startSimulation(mockConfig);

      const finalState = service.getState();
      expect(finalState.error).toBe('Server error');
      expect(finalState.isLoading).toBe(false);
    });
  });

  describe('cancelSimulation', () => {
    it('successfully cancels simulation', async () => {
      // First set up a simulation
      const simulationResponse: SimulationResponse = {
        simulation_id: 'sim_12345',
        status: 'pending',
        message: 'Simulation started'
      };

      const simulationResults: SimulationResults = {
        simulation_id: 'sim_12345',
        status: 'failed',
        config: mockConfig,
        created_at: '2023-01-01T00:00:00Z',
        error_message: 'Cancelled by user'
      };

      mockApiService.startSimulation.mockResolvedValue(simulationResponse);
      mockApiService.getSimulationStatus.mockResolvedValue({
        simulation_id: 'sim_12345',
        status: 'running',
        progress_pct: 50
      });
      mockApiService.cancelSimulation.mockResolvedValue({ message: 'Cancelled' });
      mockApiService.getSimulationResults.mockResolvedValue(simulationResults);

      service.subscribe(mockStateUpdate);
      
      // Start simulation first
      await service.startSimulation(mockConfig);
      
      // Then cancel it
      await service.cancelSimulation();

      expect(mockApiService.cancelSimulation).toHaveBeenCalledWith('sim_12345');
      
      const finalState = service.getState();
      expect(finalState.isLoading).toBe(false);
      expect(finalState.currentSimulation?.status).toBe('failed');
    });

    it('handles cancellation when no simulation is running', async () => {
      service.subscribe(mockStateUpdate);
      
      // Try to cancel without starting a simulation
      await service.cancelSimulation();

      expect(mockApiService.cancelSimulation).not.toHaveBeenCalled();
    });
  });

  describe('state management', () => {
    it('returns current state snapshot', () => {
      const state = service.getState();
      
      expect(state).toEqual({
        currentSimulation: null,
        status: null,
        isLoading: false,
        error: null,
        currentSimulationId: null
      });
    });

    it('resets state correctly', () => {
      service.subscribe(mockStateUpdate);
      
      // Manually set some state
      service.clearError();
      service.reset();
      
      const state = service.getState();
      expect(state.currentSimulation).toBeNull();
      expect(state.status).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.currentSimulationId).toBeNull();
    });

    it('clears error state', () => {
      service.subscribe(mockStateUpdate);
      service.clearError();
      
      const state = service.getState();
      expect(state.error).toBeNull();
    });
  });

  describe('validateSimulation', () => {
    it('validates simulation configuration', async () => {
      const validationResult = {
        is_valid: true,
        errors: [],
        warnings: []
      };

      mockApiService.validateSimulation.mockResolvedValue(validationResult);

      const result = await service.validateSimulation(mockConfig);

      expect(result).toEqual(validationResult);
      expect(mockApiService.validateSimulation).toHaveBeenCalledWith(mockConfig);
    });
  });

  describe('cleanup', () => {
    it('cleanup method exists and can be called', () => {
      expect(typeof service.cleanup).toBe('function');
      expect(() => service.cleanup()).not.toThrow();
    });
  });

  describe('error handling edge cases', () => {
    it('handles unknown errors gracefully', async () => {
      mockApiService.startSimulation.mockRejectedValue('Unknown error type');

      service.subscribe(mockStateUpdate);
      await service.startSimulation(mockConfig);

      const finalState = service.getState();
      expect(finalState.error).toBe('Failed to start simulation');
      expect(finalState.isLoading).toBe(false);
    });
  });
});