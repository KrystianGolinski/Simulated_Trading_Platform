import { useState, useCallback, useRef, useEffect } from 'react';
import { apiService, SimulationConfig, SimulationResults, SimulationStatusResponse } from '../services/api';

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
  const [currentSimulation, setCurrentSimulation] = useState<SimulationResults | null>(null);
  const [status, setStatus] = useState<SimulationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSimulationId, setCurrentSimulationId] = useState<string | null>(null);
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setCurrentSimulation(null);
    setStatus(null);
    setIsLoading(false);
    setError(null);
    setCurrentSimulationId(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const pollSimulationStatus = useCallback(async (simulationId: string) => {
    try {
      const statusResponse = await apiService.getSimulationStatus(simulationId);
      setStatus(statusResponse);

      if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
        // Simulation finished, get final results
        const results = await apiService.getSimulationResults(simulationId);
        setCurrentSimulation(results);
        setIsLoading(false);
        stopPolling();
      }
    } catch (err) {
      console.error('Error polling simulation status:', err);
      setError(err instanceof Error ? err.message : 'Failed to get simulation status');
      setIsLoading(false);
      stopPolling();
    }
  }, [stopPolling]);

  const startSimulation = useCallback(async (config: SimulationConfig) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentSimulation(null);
      setStatus(null);

      const response = await apiService.startSimulation(config);
      setCurrentSimulationId(response.simulation_id);

      // Start polling for status updates
      pollingIntervalRef.current = setInterval(() => {
        pollSimulationStatus(response.simulation_id);
      }, 2000); // Poll every 2 seconds

      // Initial status check
      await pollSimulationStatus(response.simulation_id);
    } catch (err) {
      console.error('Error starting simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
      setIsLoading(false);
    }
  }, [pollSimulationStatus]);

  const cancelSimulation = useCallback(async () => {
    if (!currentSimulationId) {
      return;
    }

    try {
      await apiService.cancelSimulation(currentSimulationId);
      setIsLoading(false);
      stopPolling();
      
      // Get updated results to show cancellation
      const results = await apiService.getSimulationResults(currentSimulationId);
      setCurrentSimulation(results);
    } catch (err) {
      console.error('Error cancelling simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to cancel simulation');
    }
  }, [currentSimulationId, stopPolling]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  return {
    startSimulation,
    cancelSimulation,
    currentSimulation,
    status,
    isLoading,
    error,
    clearError,
    reset,
  };
};