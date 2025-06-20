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

logger = logging.getLogger(__name__)

class SimulationEngine:
    def __init__(self):
        # Always assume Docker environment - simplified configuration
        # C++ engine is accessible via shared volume in Docker
        self.cpp_engine_path = Path("/shared/cpp-engine-build/trading_engine")
        logger.info(f"Using Docker C++ engine path: {self.cpp_engine_path}")
                    
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
        self.results_storage: Dict[str, SimulationResults] = {}
        
    def _validate_cpp_engine(self) -> Dict[str, Any]:
        # Detailed validation of C++ engine with Docker-specific error messages
        if self.cpp_engine_path is None:
            return {
                'is_valid': False,
                'error': 'C++ engine path not configured',
                'error_code': 'ENGINE_NOT_CONFIGURED',
                'suggestions': [
                    'Ensure Docker containers are running',
                    'Check Docker volume mounts are properly configured',
                    'Verify C++ engine was compiled in build container'
                ]
            }
        
        if not self.cpp_engine_path.exists():
            return {
                'is_valid': False,
                'error': f'C++ engine executable not found at {self.cpp_engine_path}',
                'error_code': 'ENGINE_FILE_NOT_FOUND',
                'suggestions': [
                    'Ensure C++ engine container has built successfully',
                    'Check Docker volume mount configuration',
                    'Verify shared volume is accessible between containers'
                ]
            }
        
        if not os.access(self.cpp_engine_path, os.X_OK):
            return {
                'is_valid': False,
                'error': f'C++ engine not executable at {self.cpp_engine_path}',
                'error_code': 'ENGINE_NOT_EXECUTABLE',
                'suggestions': [
                    'Check Docker volume mount permissions',
                    'Verify C++ engine was built with correct permissions',
                    'Ensure shared volume allows executable files'
                ]
            }
        
        # Test engine execution (local)
        try:
            result = subprocess.run(
                [str(self.cpp_engine_path), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    'is_valid': False,
                    'error': f'C++ engine test execution failed (return code: {result.returncode})',
                    'error_code': 'ENGINE_EXECUTION_FAILED',
                    'stderr': result.stderr,
                    'suggestions': [
                        'Check if all dependencies are installed',
                        'Verify the engine was compiled correctly',
                        'Check for missing shared libraries'
                    ]
                }
                
        except subprocess.TimeoutExpired:
            return {
                'is_valid': False,
                'error': 'C++ engine test execution timed out',
                'error_code': 'ENGINE_TIMEOUT',
                'suggestions': [
                    'Check if the engine is hanging',
                    'Verify system resources are available'
                ]
            }
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'C++ engine test failed: {str(e)}',
                'error_code': 'ENGINE_TEST_ERROR',
                'suggestions': [
                    'Check system logs for more details',
                    'Verify the engine binary is valid'
                ]
            }
        
        return {
            'is_valid': True,
            'error': None,
            'path': str(self.cpp_engine_path)
        }
    
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
        
        # Create simulation results object
        simulation_result = SimulationResults(
            simulation_id=simulation_id,
            status=SimulationStatus.PENDING,
            config=config,
            created_at=datetime.now()
        )
        
        self.results_storage[simulation_id] = simulation_result
        
        # Optimize simulation based on configuration
        optimization_info = await performance_optimizer.optimize_multi_symbol_simulation(config)
        logger.info(f"Simulation {simulation_id} optimization: {optimization_info}")
        
        # Start simulation in background
        asyncio.create_task(self._run_simulation(simulation_id, config, optimization_info))
        
        return simulation_id
    
    async def _run_simulation(self, simulation_id: str, config: SimulationConfig, optimization_info: Dict[str, Any] = None):
        # Run the simulation in a subprocess with optimizations
        try:
            # Update status to running
            self.results_storage[simulation_id].status = SimulationStatus.RUNNING
            self.results_storage[simulation_id].started_at = datetime.now()
            
            # Build command with optimization info
            start_time = performance_optimizer.start_timer("command_building")
            cmd = self._build_cpp_command(config)
            
            # Add performance optimizations to command
            if optimization_info and optimization_info.get("optimization") == "thread_parallel":
                cmd.extend(["--parallel-threads", str(optimization_info.get("parallel_tasks", 1))])
            
            build_time = performance_optimizer.end_timer("command_building", start_time)
            
            # Validate working directory before subprocess execution
            working_dir = self.cpp_engine_path.parent
            if not working_dir.exists() or not working_dir.is_dir():
                raise RuntimeError(f"Invalid working directory for C++ engine: {working_dir}")
            
            logger.debug(f"Starting simulation {simulation_id}: {' '.join(cmd)} (build_time: {build_time:.2f}ms)")
            
            # Run subprocess with validated working directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            # Store process for status tracking
            self.active_simulations[simulation_id] = {
                "process": process,
                "start_time": datetime.now(),
                "progress_pct": 0.0,
                "current_date": None,
                "current_value": None
            }
            
            # Read output streams manually to handle progress updates
            stdout_data = []
            stderr_data = []
            
            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    stdout_data.append(line)
            
            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    stderr_data.append(line)
                    
                    # Process progress updates
                    line_text = line.decode().strip()
                    try:
                        progress_data = json.loads(line_text)
                        if progress_data.get("type") == "progress":
                            if simulation_id in self.active_simulations:
                                sim_info = self.active_simulations[simulation_id]
                                sim_info["progress_pct"] = progress_data.get("progress_pct", 0)
                                sim_info["current_date"] = progress_data.get("current_date")
                                sim_info["current_value"] = progress_data.get("current_value")
                                
                                
                                logger.info(f"Simulation {simulation_id} progress: {progress_data.get('progress_pct', 0):.1f}%")
                    except json.JSONDecodeError:
                        # Not JSON, just regular stderr output
                        pass
            
            # Start reading both streams
            stdout_task = asyncio.create_task(read_stdout())
            stderr_task = asyncio.create_task(read_stderr())
            
            # Wait for process completion
            await process.wait()
            
            # Wait for all data to be read
            await stdout_task
            await stderr_task
            
            # Combine the data
            stdout = b''.join(stdout_data)
            stderr = b''.join(stderr_data)
            
            # Log the raw output for debugging
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            logger.error(f"Simulation {simulation_id} - Return code: {process.returncode}")
            logger.error(f"Simulation {simulation_id} - STDOUT: '{stdout_text}'")
            logger.error(f"Simulation {simulation_id} - STDERR: '{stderr_text}'")
            logger.error(f"Simulation {simulation_id} - Command was: {cmd}")
            
            if process.returncode == 0:
                # Parse results
                try:
                    if not stdout_text.strip():
                        raise json.JSONDecodeError("Empty output", "", 0)
                    result_data = json.loads(stdout_text)
                    await self._process_simulation_results(simulation_id, result_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output for simulation {simulation_id}: {e}")
                    error_msg = self._format_cpp_engine_error("JSON_PARSE_ERROR", str(e), stdout_text, stderr_text)
                    self._mark_simulation_failed(simulation_id, error_msg)
            else:
                # Enhanced error handling with specific error types
                error_msg = self._categorize_cpp_engine_error(process.returncode, stdout_text, stderr_text)
                logger.error(f"Simulation {simulation_id} failed: {error_msg}")
                self._mark_simulation_failed(simulation_id, error_msg)
                
        except Exception as e:
            logger.error(f"Exception in simulation {simulation_id}: {e}")
            self._mark_simulation_failed(simulation_id, str(e))
        finally:
            # Clean up
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
    
    async def _process_simulation_results(self, simulation_id: str, result_data: dict):
        # Process and store simulation results from engine
        try:
            simulation_result = self.results_storage[simulation_id]
            
            # Update basic results
            simulation_result.starting_capital = result_data.get("starting_capital")
            simulation_result.ending_value = result_data.get("ending_value")
            simulation_result.total_return_pct = result_data.get("total_return_pct")
            
            # Process performance metrics
            if "performance_metrics" in result_data:
                metrics_data = result_data["performance_metrics"]
                simulation_result.performance_metrics = PerformanceMetrics(
                    total_return_pct=metrics_data.get("total_return_pct", 0.0),
                    sharpe_ratio=metrics_data.get("sharpe_ratio"),
                    max_drawdown_pct=metrics_data.get("max_drawdown_pct", 0.0),
                    win_rate=metrics_data.get("win_rate", 0.0),
                    total_trades=metrics_data.get("total_trades", 0),
                    winning_trades=metrics_data.get("winning_trades", 0),
                    losing_trades=metrics_data.get("losing_trades", 0)
                )
            
            # Process trades
            if "trades" in result_data:
                trades = []
                trades_data = result_data["trades"]
                # Handle case where trades might be an integer (count) or array
                if isinstance(trades_data, list):
                    for trade_data in trades_data:
                        trade = TradeRecord(
                            date=trade_data["date"],
                            symbol=trade_data["symbol"],
                            action=trade_data["action"],
                            shares=trade_data["shares"],
                            price=trade_data["price"],
                            total_value=trade_data["total_value"]
                        )
                        trades.append(trade)
                # If trades is just a count (integer), leave trades as empty list
                simulation_result.trades = trades
            
            # Process equity curve
            simulation_result.equity_curve = result_data.get("equity_curve", [])
            
            # Mark as completed
            simulation_result.status = SimulationStatus.COMPLETED
            simulation_result.completed_at = datetime.now()
            
            logger.info(f"Simulation {simulation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process results for simulation {simulation_id}: {e}")
            self._mark_simulation_failed(simulation_id, f"Result processing error: {e}")
    
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
        if simulation_id in self.results_storage:
            self.results_storage[simulation_id].status = SimulationStatus.FAILED
            self.results_storage[simulation_id].error_message = error_message
            self.results_storage[simulation_id].completed_at = datetime.now()
    
    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationResults]:
        # Get current status of a simulation
        return self.results_storage.get(simulation_id)
    
    def get_simulation_progress(self, simulation_id: str) -> Dict[str, Any]:
        # Get detailed progress information for a running simulation
        if simulation_id not in self.results_storage:
            return {"error": "Simulation not found"}
        
        result = self.results_storage[simulation_id]
        progress_info = {
            "simulation_id": simulation_id,
            "status": result.status.value,
            "progress_pct": None,
            "current_date": None,
            "elapsed_time": None,
            "estimated_remaining": None
        }
        
        
        if simulation_id in self.active_simulations:
            sim_info = self.active_simulations[simulation_id]
            start_time = sim_info["start_time"]
            elapsed = (datetime.now() - start_time).total_seconds()
            progress_info["elapsed_time"] = elapsed
            
            # Use actual progress from C++ engine
            actual_progress = sim_info.get("progress_pct", 0)
            progress_info["progress_pct"] = actual_progress
            progress_info["current_date"] = sim_info.get("current_date")
            progress_info["current_value"] = sim_info.get("current_value")
            
        elif result.status.value == "completed":
            # For completed simulations, show 100% progress
            progress_info["progress_pct"] = 100.0
            if result.completed_at and result.started_at:
                progress_info["elapsed_time"] = (result.completed_at - result.started_at).total_seconds()
        
        return progress_info
    
    def list_simulations(self) -> Dict[str, SimulationResults]:
        # List all simulations
        return self.results_storage.copy()
    
    async def cancel_simulation(self, simulation_id: str) -> bool:
        # Cancel a running simulation
        if simulation_id in self.active_simulations:
            try:
                process = self.active_simulations[simulation_id]["process"]
                process.terminate()
                
                # Wait for termination with timeout
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if terminate didn't work
                    process.kill()
                    await process.wait()
                
                self._mark_simulation_failed(simulation_id, "Simulation cancelled by user")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel simulation {simulation_id}: {e}")
                return False
        
        return False

# Global simulation engine instance
simulation_engine = SimulationEngine()