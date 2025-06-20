import asyncio
import json
import uuid
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging

from models import SimulationConfig, SimulationResults, SimulationStatus, PerformanceMetrics, TradeRecord
from performance_optimizer import performance_optimizer, PerformanceOptimizer
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
    
    def _build_cpp_command(self, config: SimulationConfig) -> list:
        # Build command line arguments for engine
        cmd = [
            str(self.cpp_engine_path),
            "--simulate",  # Use simulate mode for JSON output
            "--progress"   # Always enable progress reporting
        ]
        
        # Add symbols (take first symbol for now, multi-symbol support can be added later)
        if config.symbols:
            cmd.extend(["--symbol", config.symbols[0]])
        
        # Add date range
        cmd.extend([
            "--start", config.start_date.isoformat(),
            "--end", config.end_date.isoformat()
        ])
        
        # Add starting capital
        cmd.extend(["--capital", str(int(config.starting_capital))])
        
        # Add strategy-specific parameters
        if config.strategy.value == "ma_crossover":
            if config.short_ma:
                cmd.extend(["--short-ma", str(config.short_ma)])
            if config.long_ma:
                cmd.extend(["--long-ma", str(config.long_ma)])
        elif config.strategy.value == "rsi":
            if config.rsi_period:
                cmd.extend(["--rsi-period", str(config.rsi_period)])
            if config.rsi_oversold:
                cmd.extend(["--rsi-oversold", str(config.rsi_oversold)])
            if config.rsi_overbought:
                cmd.extend(["--rsi-overbought", str(config.rsi_overbought)])
        
        return cmd
    
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
                simulation_id, config, optimization_info
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
    
    def _categorize_cpp_engine_error(self, return_code: int, stdout: str, stderr: str) -> str:
        # Categorize C++ engine errors and provide helpful messages
        # Common error patterns
        if 'database' in stderr.lower() or 'connection' in stderr.lower():
            return self._format_cpp_engine_error(
                "DATABASE_ERROR",
                "Database connection failed in C++ engine",
                stdout, stderr,
                suggestions=[
                    "Check if PostgreSQL is running",
                    "Verify database connection parameters",
                    "Ensure database contains required stock data"
                ]
            )
        
        if 'symbol' in stderr.lower() and 'not found' in stderr.lower():
            return self._format_cpp_engine_error(
                "SYMBOL_ERROR",
                "Stock symbol not found in database",
                stdout, stderr,
                suggestions=[
                    "Verify the stock symbol exists in the database",
                    "Check if the symbol is spelled correctly"
                ]
            )
        
        if 'insufficient data' in stderr.lower() or 'no data' in stderr.lower():
            return self._format_cpp_engine_error(
                "DATA_ERROR", 
                "Insufficient data for the specified date range",
                stdout, stderr,
                suggestions=[
                    "Try a different date range",
                    "Check if data exists for the selected period"
                ]
            )
        
        if return_code == -11:  # SIGSEGV - Segmentation fault
            return self._format_cpp_engine_error(
                "CRASH_ERROR",
                "C++ engine crashed (segmentation fault)",
                stdout, stderr,
                suggestions=[
                    "This is likely a bug in the C++ engine",
                    "Try with different parameters",
                    "Check system resources"
                ]
            )
        
        if return_code == -15:  # SIGTERM - Signal terminate
            return self._format_cpp_engine_error(
                "TIMEOUT_ERROR",
                "C++ engine was terminated (likely timeout)",
                stdout, stderr,
                suggestions=[
                    "Try a shorter date range",
                    "Check system resources"
                ]
            )
        
        # Generic error
        return self._format_cpp_engine_error(
            "UNKNOWN_ERROR",
            f"C++ engine failed with return code {return_code}",
            stdout, stderr
        )
    
    def _format_cpp_engine_error(self, error_type: str, message: str, 
                                stdout: str, stderr: str, 
                                suggestions: List[str] = None) -> str:
        # Format a comprehensive error message for C++ engine failures
        error_info = {
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        
        if suggestions:
            error_info["suggestions"] = suggestions
        
        # Add relevant output (truncated for conciseness)
        if stderr and len(stderr.strip()) > 0:
            error_info["stderr"] = stderr[:500] + "..." if len(stderr) > 500 else stderr
        
        if stdout and len(stdout.strip()) > 0:
            error_info["stdout"] = stdout[:500] + "..." if len(stdout) > 500 else stdout
        
        return json.dumps(error_info, indent=2)
    
    def _mark_simulation_failed(self, simulation_id: str, error_message: str):
        # Mark simulation as failed with error message
        self.result_processor.mark_simulation_failed(simulation_id, error_message)
    
    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationResults]:
        # Get current status of a simulation
        return self.result_processor.get_simulation_result(simulation_id)
    
    def get_simulation_progress(self, simulation_id: str) -> Dict[str, Any]:
        # Get detailed progress information for a running simulation
        result = self.result_processor.get_simulation_result(simulation_id)
        if not result:
            return {"error": "Simulation not found"}
        progress_info = {
            "simulation_id": simulation_id,
            "status": result.status.value,
            "progress_pct": None,
            "current_date": None,
            "elapsed_time": None,
            "estimated_remaining": None
        }
        
        
        # Get progress from execution service
        execution_progress = self.execution_service.get_simulation_progress(simulation_id)
        if execution_progress["status"] == "running":
            progress_info["progress_pct"] = execution_progress.get("progress_pct", 0)
            progress_info["current_date"] = execution_progress.get("current_date")
            progress_info["current_value"] = execution_progress.get("current_value")
            
            start_time = execution_progress.get("start_time")
            if start_time:
                elapsed = (datetime.now() - start_time).total_seconds()
                progress_info["elapsed_time"] = elapsed
            
        elif result.status.value == "completed":
            # For completed simulations, show 100% progress
            progress_info["progress_pct"] = 100.0
            if result.completed_at and result.started_at:
                progress_info["elapsed_time"] = (result.completed_at - result.started_at).total_seconds()
        
        return progress_info
    
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