import { apiService } from '../api';
import type { 
  SimulationConfig, 
  SimulationResults, 
  SimulationStatusResponse 
} from '../api';

// Focused service for simulation API operations
export class SimulationAPI {
  async startSimulation(config: SimulationConfig) {
    return apiService.startSimulation(config);
  }

  async cancelSimulation(simulationId: string) {
    return apiService.cancelSimulation(simulationId);
  }

  async getSimulationStatus(simulationId: string): Promise<SimulationStatusResponse> {
    return apiService.getSimulationStatus(simulationId);
  }

  async getSimulationResults(simulationId: string): Promise<SimulationResults> {
    return apiService.getSimulationResults(simulationId);
  }

  async validateSimulation(config: SimulationConfig) {
    return apiService.validateSimulation(config);
  }
}

export const simulationAPI = new SimulationAPI();