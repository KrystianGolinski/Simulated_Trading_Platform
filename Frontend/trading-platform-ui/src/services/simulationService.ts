import { apiService } from './api';
import type { 
  SimulationConfig, 
  SimulationResults, 
  SimulationStatusResponse 
} from './api';

// Enhanced unified simulation state interface
export interface SimulationState {
  currentSimulation: SimulationResults | null;
  status: SimulationStatusResponse | null;
  isLoading: boolean;
  error: string | null;
  currentSimulationId: string | null;
}

// Callback type for state updates
export type SimulationStateCallback = (state: SimulationState) => void;

export class ConsolidatedSimulationService {
  private statusPollingInterval?: NodeJS.Timeout;
  private onStateUpdate?: SimulationStateCallback;
  private currentState: SimulationState = {
    currentSimulation: null,
    status: null,
    isLoading: false,
    error: null,
    currentSimulationId: null
  };

  // Subscribe to state updates (for hooks)
  subscribe(callback: SimulationStateCallback): void {
    this.onStateUpdate = callback;
  }

  // Get current state snapshot
  getState(): SimulationState {
    return { ...this.currentState };
  }

  // Main method: start simulation with validation
  async startSimulation(config: SimulationConfig): Promise<void> {
    try {
      this.updateState({
        isLoading: true,
        error: null,
        currentSimulation: null,
        status: null,
        currentSimulationId: null
      });

      const response = await apiService.startSimulation(config);
      
      this.updateState({
        currentSimulationId: response.simulation_id,
        isLoading: true
      });

      // Start status polling
      this.startStatusPolling(response.simulation_id);
      
      // Initial status check
      await this.pollSimulationStatus(response.simulation_id);
    } catch (error) {
      console.error('Error starting simulation:', error);
      this.updateState({
        error: error instanceof Error ? error.message : 'Failed to start simulation',
        isLoading: false
      });
    }
  }

  // Cancel running simulation
  async cancelSimulation(): Promise<void> {
    if (!this.currentState.currentSimulationId) {
      return;
    }

    try {
      await apiService.cancelSimulation(this.currentState.currentSimulationId);
      this.updateState({ isLoading: false });
      this.stopStatusPolling();
      
      // Get updated results to show cancellation
      const results = await apiService.getSimulationResults(this.currentState.currentSimulationId);
      this.updateState({ currentSimulation: results });
    } catch (error) {
      console.error('Error cancelling simulation:', error);
      this.updateState({
        error: error instanceof Error ? error.message : 'Failed to cancel simulation'
      });
    }
  }

  // Reset simulation state
  reset(): void {
    this.stopStatusPolling();
    this.updateState({
      currentSimulation: null,
      status: null,
      isLoading: false,
      error: null,
      currentSimulationId: null
    });
  }

  // Clear error state
  clearError(): void {
    this.updateState({ error: null });
  }

  // Validate simulation configuration
  async validateSimulation(config: SimulationConfig) {
    return apiService.validateSimulation(config);
  }

  // Private poll simulation status
  private async pollSimulationStatus(simulationId: string): Promise<void> {
    try {
      const statusResponse = await apiService.getSimulationStatus(simulationId);
      this.updateState({ status: statusResponse });

      if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
        // Simulation finished, get final results
        const results = await apiService.getSimulationResults(simulationId);
        this.updateState({
          currentSimulation: results,
          isLoading: false
        });
        this.stopStatusPolling();
      }
    } catch (error) {
      console.error('Error polling simulation status:', error);
      this.updateState({
        error: error instanceof Error ? error.message : 'Failed to get simulation status',
        isLoading: false
      });
      this.stopStatusPolling();
    }
  }

  // Private start status polling interval
  private startStatusPolling(simulationId: string): void {
    this.statusPollingInterval = setInterval(() => {
      this.pollSimulationStatus(simulationId);
    }, 2000); // Poll every 2 seconds
  }

  // Private stop status polling interval
  private stopStatusPolling(): void {
    if (this.statusPollingInterval) {
      clearInterval(this.statusPollingInterval);
      this.statusPollingInterval = undefined;
    }
  }

  // Private update internal state and notify subscribers
  private updateState(partialState: Partial<SimulationState>): void {
    this.currentState = { ...this.currentState, ...partialState };
    if (this.onStateUpdate) {
      this.onStateUpdate(this.currentState);
    }
  }

  // Cleanup method
  cleanup(): void {
    this.stopStatusPolling();
    this.onStateUpdate = undefined;
  }
}

export const simulationService = new ConsolidatedSimulationService();