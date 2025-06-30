import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
import logging

from models import SimulationConfig, SimulationResults, SimulationStatus
from performance_optimizer import performance_optimizer
from services.execution_service import ExecutionService
from services.result_processor import ResultProcessor
from services.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class SimulationEngine:
    def __init__(self):
        # C++ engine is accessible via shared volume in Docker
        self.cpp_engine_path = Path("/shared/trading_engine")
        logger.info(f"Using shared C++ engine path: {self.cpp_engine_path}")
        
        # Initialize separated services
        self.execution_service = ExecutionService(self.cpp_engine_path)
        self.result_processor = ResultProcessor()
        self.error_handler = ErrorHandler()
        
    def _validate_cpp_engine(self) -> Dict[str, Any]:
        return self.execution_service.validate_cpp_engine()
    
    
    async def start_simulation(self, config: SimulationConfig) -> str:
        # Start a new simulation and return simulation ID
        # Enhanced engine validation with detailed error messages
        engine_validation = self._validate_cpp_engine()
        if not engine_validation['is_valid']:
            raise RuntimeError(f"C++ trading engine validation failed: {engine_validation['error']}")
        
        simulation_id = str(uuid.uuid4())
        
        # Initialize simulation result using result processor
        self.result_processor.initialize_simulation_result(simulation_id, config)
        
        # Optimize simulation based on configuration
        optimization_info = await performance_optimizer.optimize_multi_symbol_simulation(config)
        logger.info(f"Simulation {simulation_id} optimization: {optimization_info}")
        
        # Start simulation in background
        asyncio.create_task(self._run_simulation(simulation_id, config, optimization_info))
        
        return simulation_id
    
    async def _run_simulation(self, simulation_id: str, config: SimulationConfig, optimization_info: Dict[str, Any] = None):
        try:
            # Update status to running
            self.result_processor.update_simulation_status(
                simulation_id, SimulationStatus.RUNNING, datetime.now()
            )
            
            # Execute simulation using execution service
            execution_result = await self.execution_service.execute_simulation(
                simulation_id, config
            )
            
            # Process results based on execution outcome
            if execution_result["return_code"] == 0:
                try:
                    result_data = self.result_processor.parse_json_result(execution_result["stdout"])
                    if self.result_processor.validate_result_data(result_data):
                        self.result_processor.process_simulation_results(simulation_id, result_data)
                    else:
                        error = self.error_handler.create_validation_error(
                            "Invalid result data structure",
                            {"stdout_preview": execution_result["stdout"][:200]}
                        )
                        self.result_processor.mark_simulation_failed(simulation_id, error.message)
                except json.JSONDecodeError as e:
                    error = self.error_handler.create_json_parse_error(str(e), execution_result["stdout"])
                    self.result_processor.mark_simulation_failed(simulation_id, error.message)
            else:
                # Handle execution failure
                error = self.error_handler.categorize_cpp_engine_error(
                    execution_result["return_code"],
                    execution_result["stdout"],
                    execution_result["stderr"]
                )
                self.result_processor.mark_simulation_failed(simulation_id, error.message)
                
        except Exception as e:
            error = self.error_handler.create_generic_error(
                f"Unexpected error in simulation {simulation_id}: {str(e)}",
                {"simulation_id": simulation_id}
            )
            self.result_processor.mark_simulation_failed(simulation_id, error.message)
    
    
    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationResults]:
        # Get current status of a simulation
        return self.result_processor.get_simulation_result(simulation_id)
    
    def get_simulation_progress(self, simulation_id: str) -> Dict[str, Any]:
        # Delegate progress tracking to execution service
        return self.execution_service.get_simulation_progress(simulation_id)
    
    def list_simulations(self) -> Dict[str, SimulationResults]:
        # List all simulations
        return self.result_processor.get_all_simulation_results()
    
    async def cancel_simulation(self, simulation_id: str) -> bool:
        # Cancel a running simulation using the execution service
        try:
            # Try to cancel the running process
            cancelled = await self.execution_service.cancel_simulation(simulation_id)
            
            if cancelled:
                # Mark as failed in result processor
                self.result_processor.mark_simulation_failed(simulation_id, "Simulation cancelled by user")
                logger.info(f"Simulation {simulation_id} successfully cancelled")
                return True
            else:
                # Process not found or already completed, just mark as cancelled
                self.result_processor.mark_simulation_failed(simulation_id, "Simulation cancellation requested")
                logger.info(f"Simulation {simulation_id} marked as cancelled (process not active)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel simulation {simulation_id}: {e}")
            return False

# Global simulation engine instance
simulation_engine = SimulationEngine()