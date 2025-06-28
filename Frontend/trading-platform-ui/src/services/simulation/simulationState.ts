import type { 
  SimulationResults, 
  SimulationStatusResponse 
} from '../api';

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

// Focused service for simulation state management
export class SimulationStateManager {
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

  // Unsubscribe from state updates
  unsubscribe(): void {
    this.onStateUpdate = undefined;
  }

  // Get current state snapshot
  getState(): SimulationState {
    return { ...this.currentState };
  }

  // Update state and notify subscribers
  updateState(partialState: Partial<SimulationState>): void {
    this.currentState = { ...this.currentState, ...partialState };
    if (this.onStateUpdate) {
      this.onStateUpdate(this.currentState);
    }
  }

  // Reset simulation state
  reset(): void {
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

  // Set loading state
  setLoading(isLoading: boolean): void {
    this.updateState({ isLoading });
  }

  // Set error state
  setError(error: string | null): void {
    this.updateState({ error });
  }

  // Set simulation ID
  setSimulationId(simulationId: string | null): void {
    this.updateState({ currentSimulationId: simulationId });
  }

  // Set simulation results
  setSimulationResults(results: SimulationResults | null): void {
    this.updateState({ currentSimulation: results });
  }

  // Set simulation status
  setSimulationStatus(status: SimulationStatusResponse | null): void {
    this.updateState({ status });
  }

  // Check if simulation is running
  isSimulationRunning(): boolean {
    return this.currentState.isLoading || 
           (this.currentState.status?.status === 'running' || 
            this.currentState.status?.status === 'pending');
  }

  // Check if simulation is completed
  isSimulationCompleted(): boolean {
    return this.currentState.status?.status === 'completed' || 
           this.currentState.status?.status === 'failed';
  }
}

export const simulationStateManager = new SimulationStateManager();