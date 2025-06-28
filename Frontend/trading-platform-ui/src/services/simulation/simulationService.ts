import { simulationAPI } from './simulationAPI';
import { simulationStateManager, SimulationStateCallback, SimulationState } from './simulationState';
import { pollingService } from './pollingService';
import type { SimulationConfig } from '../api';

// Orchestrator service that coordinates API, state, and polling services
export class SimulationService {
  // Delegate state management
  subscribe(callback: SimulationStateCallback): void {
    simulationStateManager.subscribe(callback);
  }

  unsubscribe(): void {
    simulationStateManager.unsubscribe();
  }

  getState(): SimulationState {
    return simulationStateManager.getState();
  }

  // Main method: start simulation with validation
  async startSimulation(config: SimulationConfig): Promise<void> {
    try {
      simulationStateManager.updateState({
        isLoading: true,
        error: null,
        currentSimulation: null,
        status: null,
        currentSimulationId: null
      });

      const response = await simulationAPI.startSimulation(config);
      
      simulationStateManager.updateState({
        currentSimulationId: response.simulation_id,
        isLoading: true
      });

      // Start status polling
      this.startStatusPolling(response.simulation_id);
      
      // Initial status check
      await this.pollSimulationStatus(response.simulation_id);
    } catch (error) {
      console.error('Error starting simulation:', error);
      simulationStateManager.updateState({
        error: error instanceof Error ? error.message : 'Failed to start simulation',
        isLoading: false
      });
    }
  }

  // Cancel running simulation
  async cancelSimulation(): Promise<void> {
    const currentState = simulationStateManager.getState();
    if (!currentState.currentSimulationId) {
      return;
    }

    try {
      await simulationAPI.cancelSimulation(currentState.currentSimulationId);
      simulationStateManager.setLoading(false);
      pollingService.stopPolling();
      
      // Get updated results to show cancellation
      const results = await simulationAPI.getSimulationResults(currentState.currentSimulationId);
      simulationStateManager.setSimulationResults(results);
    } catch (error) {
      console.error('Error cancelling simulation:', error);
      simulationStateManager.setError(
        error instanceof Error ? error.message : 'Failed to cancel simulation'
      );
    }
  }

  // Reset simulation state
  reset(): void {
    pollingService.stopPolling();
    simulationStateManager.reset();
  }

  // Clear error state
  clearError(): void {
    simulationStateManager.clearError();
  }

  // Validate simulation configuration
  async validateSimulation(config: SimulationConfig) {
    return simulationAPI.validateSimulation(config);
  }

  // Private poll simulation status
  private async pollSimulationStatus(simulationId: string): Promise<void> {
    try {
      const statusResponse = await simulationAPI.getSimulationStatus(simulationId);
      simulationStateManager.setSimulationStatus(statusResponse);

      if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
        // Simulation finished, get final results
        const results = await simulationAPI.getSimulationResults(simulationId);
        simulationStateManager.updateState({
          currentSimulation: results,
          isLoading: false
        });
        pollingService.stopPolling();
      }
    } catch (error) {
      console.error('Error polling simulation status:', error);
      simulationStateManager.updateState({
        error: error instanceof Error ? error.message : 'Failed to get simulation status',
        isLoading: false
      });
      pollingService.stopPolling();
    }
  }

  // Private start status polling
  private startStatusPolling(simulationId: string): void {
    pollingService.startPolling(() => this.pollSimulationStatus(simulationId));
  }

  // Cleanup method
  cleanup(): void {
    pollingService.cleanup();
    simulationStateManager.unsubscribe();
  }
}

export const simulationService = new SimulationService();

// Export types for convenience
export type { SimulationState, SimulationStateCallback };