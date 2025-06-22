import { useState, useCallback, useEffect } from 'react';
import { SimulationConfig, SimulationResults, SimulationStatusResponse } from '../services/api';
import { simulationService, SimulationState } from '../services/simulationService';

export interface UseSimulationReturn {
  startSimulation: (config: SimulationConfig) => Promise<void>;
  cancelSimulation: () => Promise<void>;
  currentSimulation: SimulationResults | null;
  status: SimulationStatusResponse | null;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  reset: () => void;
}

export const useSimulation = (): UseSimulationReturn => {
  // Initialize state from service
  const [state, setState] = useState<SimulationState>(() => simulationService.getState());

  // Subscribe to service state updates
  useEffect(() => {
    simulationService.subscribe(setState);
    
    // Cleanup subscription and service on unmount
    return () => {
      simulationService.cleanup();
    };
  }, []);

  // Memoized service methods
  const startSimulation = useCallback(async (config: SimulationConfig) => {
    await simulationService.startSimulation(config);
  }, []);

  const cancelSimulation = useCallback(async () => {
    await simulationService.cancelSimulation();
  }, []);

  const clearError = useCallback(() => {
    simulationService.clearError();
  }, []);

  const reset = useCallback(() => {
    simulationService.reset();
  }, []);

  return {
    startSimulation,
    cancelSimulation,
    currentSimulation: state.currentSimulation,
    status: state.status,
    isLoading: state.isLoading,
    error: state.error,
    clearError,
    reset,
  };
};