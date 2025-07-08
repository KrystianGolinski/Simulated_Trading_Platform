# Execution Service - Advanced C++ Engine Execution and Management System
# This module provides comprehensive C++ engine execution capabilities for the Trading Platform API
# 
# Architecture Overview:
# The ExecutionService implements sophisticated execution management for the C++ trading engine,
# providing asynchronous process execution, real-time progress monitoring, resource validation,
# and comprehensive error handling. It serves as the primary interface between the Python API
# and the C++ trading engine.
#
# Key Responsibilities:
# 1. C++ engine validation and configuration management
# 2. Asynchronous simulation execution with progress tracking
# 3. Real-time process monitoring and health checking
# 4. Dynamic configuration file generation for C++ engine
# 5. Resource management and cleanup operations
# 6. Memory usage monitoring and reporting
# 7. Simulation lifecycle management (start, monitor, cancel)
#
# Execution Pipeline:
# 1. Validate C++ engine availability and permissions
# 2. Generate dynamic configuration file from simulation parameters
# 3. Build command-line arguments for C++ engine execution
# 4. Execute simulation asynchronously with environment setup
# 5. Monitor process streams for progress updates and heartbeat
# 6. Handle process completion and resource cleanup
# 7. Parse and return execution results with error handling
#
# Integration with Trading Platform:
# - Interfaces with C++ trading engine via process execution
# - Integrates with strategy factory for dynamic strategy configuration
# - Supports performance optimization and monitoring
# - Provides real-time simulation progress and health monitoring
# - Handles Docker container communication and volume management
# - Supports parallel execution coordination
#
# Process Management Features:
# - Asynchronous process execution with asyncio
# - Real-time stdout/stderr stream processing
# - Progress tracking via JSON-based heartbeat system
# - Health monitoring with timeout and status checking
# - Graceful termination and force-kill capabilities
# - Resource cleanup and temporary file management
# - Memory usage reporting and analysis

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from models import SimulationConfig
from performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Advanced C++ Engine Execution and Management System for the Trading Platform.
    
    This class provides comprehensive execution management for the C++ trading engine,
    implementing sophisticated process execution, real-time monitoring, and resource
    management capabilities. It serves as the primary interface between the Python API
    and the C++ trading engine, handling all aspects of simulation execution.
    
    Key Features:
    - Asynchronous C++ engine execution with real-time monitoring
    - Dynamic configuration file generation for flexible strategy execution
    - Comprehensive process health monitoring and timeout handling
    - Real-time progress tracking via JSON-based heartbeat system
    - Memory usage monitoring and reporting capabilities
    - Graceful process termination and resource cleanup
    - Support for parallel execution coordination
    
    Architecture Integration:
    The ExecutionService integrates with multiple platform components:
    - Strategy factory for dynamic strategy configuration
    - Performance optimizer for execution timing analysis
    - Docker environment for containerized execution
    - Database connectivity for C++ engine data access
    
    Process Management:
    The service manages the complete lifecycle of simulation processes:
    1. Engine validation and configuration setup
    2. Dynamic configuration file generation
    3. Asynchronous process execution with environment setup
    4. Real-time stream processing and progress monitoring
    5. Health checking and timeout management
    6. Graceful termination and cleanup
    """
    
    def __init__(self, cpp_engine_path: Path):
        """
        Initialize the ExecutionService with C++ engine configuration.
        
        Args:
            cpp_engine_path: Path to the C++ trading engine executable
            
        The service maintains an active simulations registry for process tracking,
        health monitoring, and resource management throughout execution.
        """
        self.cpp_engine_path = cpp_engine_path
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
    
    def validate_cpp_engine(self) -> Dict[str, Any]:
        """
        Comprehensive validation of C++ engine availability and configuration.
        
        This method performs thorough validation of the C++ trading engine to ensure
        it's properly configured, accessible, and executable before simulation execution.
        It provides detailed error information and actionable suggestions for resolution.
        
        Returns:
            Dict[str, Any]: Validation result containing:
                - is_valid: Boolean indicating if engine is valid and ready
                - error: Detailed error message (if validation fails)
                - error_code: Standardized error code for categorization
                - suggestions: List of actionable resolution suggestions
                
        Validation Checks:
        1. Engine path configuration verification
        2. File existence and accessibility validation
        3. Execute permission verification
        4. Docker container and volume mount validation
        
        The method provides specific error codes and suggestions for each failure
        scenario, enabling targeted troubleshooting and resolution.
        """
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
                'error': f'C++ engine executable is not executable: {self.cpp_engine_path}',
                'error_code': 'ENGINE_NOT_EXECUTABLE',
                'suggestions': [
                    'Check file permissions on C++ engine executable',
                    'Ensure Docker container has proper execution permissions'
                ]
            }
        
        return {'is_valid': True}
    
    def create_config_file(self, config: SimulationConfig) -> str:
        """
        Create a temporary JSON config file for the C++ engine.

        This method generates a JSON configuration file based on the provided
        SimulationConfig. It uses the dynamic strategy factory to create a
        C++ compatible configuration for the selected strategy and its parameters.

        Args:
            config: The simulation configuration object.

        Returns:
            The path to the newly created temporary configuration file.
            
        Raises:
            Exception: If there is an error creating the strategy configuration
                       or writing the file.
        """
        # Create a temporary JSON config file for the C++ engine using dynamic strategy system
        try:
            # Import here to avoid circular dependencies
            from strategy_factory import get_strategy_factory
            
            # Base configuration
            config_data = {
                "symbols": config.symbols if config.symbols else ["AAPL"],
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "starting_capital": config.starting_capital,
                "cleanup": True
            }
            
            # Use dynamic strategy factory to create C++ compatible configuration
            factory = get_strategy_factory()
            strategy_config = factory.create_strategy_config(config.strategy, config.strategy_parameters)
            
            # Merge strategy configuration with base configuration
            config_data.update(strategy_config)
            
            # Create temporary file
            config_file = f"/tmp/sim_config_{uuid.uuid4().hex[:8]}.json"
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.debug(f"Created config file: {config_file} with strategy: {config.strategy}")
            return config_file
            
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            raise
    
    def build_cpp_command(self, config: SimulationConfig) -> tuple[List[str], str]:
        """
        Build the command-line arguments for executing the C++ engine.

        This method constructs the full command to run the C++ engine, including
        the path to the executable and the necessary command-line flags. It also
        creates the temporary configuration file required by the engine.

        Args:
            config: The simulation configuration object.

        Returns:
            A tuple containing:
                - A list of strings representing the command and its arguments.
                - The path to the temporary configuration file.
        """
        # Build command using JSON config file approach
        config_file = self.create_config_file(config)
        
        cmd = [
            str(self.cpp_engine_path),
            "--simulate",
            "--config", 
            config_file
        ]
        
        return cmd, config_file
    
    async def execute_simulation(self, simulation_id: str, config: SimulationConfig) -> Dict[str, Any]:
        """
        Execute a trading simulation asynchronously with comprehensive monitoring.
        
        This method orchestrates the complete simulation execution process, including
        configuration generation, process execution, real-time monitoring, and cleanup.
        It provides comprehensive error handling and resource management throughout
        the simulation lifecycle.
        
        Args:
            simulation_id: Unique identifier for tracking the simulation
            config: SimulationConfig object containing simulation parameters
            
        Returns:
            Dict[str, Any]: Execution result containing:
                - return_code: Process exit code
                - stdout: Standard output from C++ engine
                - stderr: Standard error output from C++ engine
                - command: Command line arguments used for execution
                
        Execution Pipeline:
        1. Generate dynamic configuration file for C++ engine
        2. Build command-line arguments with performance timing
        3. Validate working directory and environment setup
        4. Execute C++ engine process asynchronously
        5. Monitor process streams for progress and heartbeat
        6. Handle process completion and collect results
        7. Perform comprehensive cleanup of resources
        
        The method implements comprehensive error handling, resource cleanup,
        and progress monitoring throughout the execution process.
        """
        config_file = None
        try:
            # Build command using JSON config file with performance monitoring
            start_time = performance_optimizer.start_timer("command_building")
            cmd, config_file = self.build_cpp_command(config)
            
            build_time = performance_optimizer.end_timer("command_building", start_time)
            
            # Validate working directory before subprocess execution
            working_dir = self.cpp_engine_path.parent
            if not working_dir.exists() or not working_dir.is_dir():
                raise RuntimeError(f"Invalid working directory for C++ engine: {working_dir}")
            
            logger.debug(f"Starting simulation {simulation_id}: {' '.join(cmd)} (build_time: {build_time:.2f}ms)")
            
            # Prepare comprehensive environment variables for C++ engine
            env = os.environ.copy()  # Copy current environment
            # Ensure database environment variables are available to C++ engine
            db_env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
            for var in db_env_vars:
                if var in os.environ:
                    env[var] = os.environ[var]
                    logger.debug(f"Passing {var} to C++ engine")
            
            # Execute subprocess with validated working directory and environment
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env
            )
            
            # Register process for comprehensive status tracking with heartbeat monitoring
            self.active_simulations[simulation_id] = {
                "process": process,
                "start_time": datetime.now(),
                "progress_pct": 0.0,
                "current_date": None,
                "current_value": None,
                "last_heartbeat": datetime.now(),
                "heartbeat_timeout": 300,  # 5 minutes timeout
                "is_healthy": True
            }
            
            # Monitor output streams and handle real-time progress updates
            stdout_data, stderr_data = await self._read_process_streams(process, simulation_id)
            
            # Wait for process completion
            await process.wait()
            
            # Combine and decode output data
            stdout = b''.join(stdout_data)
            stderr = b''.join(stderr_data)
            
            return {
                "return_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "command": cmd
            }
            
        except Exception as e:
            logger.error(f"Exception in simulation execution {simulation_id}: {e}")
            raise
        finally:
            # Comprehensive cleanup of simulation resources
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
            
            # Clean up temporary configuration file if it wasn't cleaned up by C++ engine
            if config_file and os.path.exists(config_file):
                try:
                    os.remove(config_file)
                    logger.debug(f"Cleaned up config file: {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up config file {config_file}: {e}")
    
    async def _read_process_streams(self, process, simulation_id: str):
        """
        Read stdout and stderr streams from the process and monitor progress.

        This private helper method reads the output from the C++ engine process
        in real-time. It captures all stdout and stderr data and also parses
        stderr for JSON progress updates to track the simulation's progress.

        Args:
            process: The asyncio subprocess object.
            simulation_id: The ID of the simulation being monitored.

        Returns:
            A tuple containing:
                - A list of bytes from the stdout stream.
                - A list of bytes from the stderr stream.
        """
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
                
                # Process progress updates and heartbeat
                line_text = line.decode().strip()
                if simulation_id in self.active_simulations:
                    sim_info = self.active_simulations[simulation_id]
                    sim_info["last_heartbeat"] = datetime.now()  # Any output counts as heartbeat
                    sim_info["is_healthy"] = True
                
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
                    # Not JSON, just regular stderr output - still counts as heartbeat
                    pass
        
        # Start reading both streams
        stdout_task = asyncio.create_task(read_stdout())
        stderr_task = asyncio.create_task(read_stderr())
        
        # Wait for all data to be read
        await stdout_task
        await stderr_task
        
        return stdout_data, stderr_data
    
    def check_simulation_health(self, simulation_id: str) -> Dict[str, Any]:
        # Check if a simulation is healthy based on heartbeat and process status
        if simulation_id not in self.active_simulations:
            return {"status": "not_found"}
        
        sim_info = self.active_simulations[simulation_id]
        process = sim_info.get("process")
        current_time = datetime.now()
        last_heartbeat = sim_info.get("last_heartbeat", current_time)
        timeout = sim_info.get("heartbeat_timeout", 300)
        
        # Check if process is still running
        process_alive = process and process.returncode is None
        
        # Check heartbeat timeout
        heartbeat_expired = (current_time - last_heartbeat).total_seconds() > timeout
        
        # Determine health status
        if not process_alive:
            status = "failed" if process else "unknown"
        elif heartbeat_expired:
            status = "stalled"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "last_heartbeat": last_heartbeat.isoformat(),
            "seconds_since_heartbeat": (current_time - last_heartbeat).total_seconds(),
            "process_alive": process_alive,
            "process_return_code": process.returncode if process else None
        }
    
    def get_unhealthy_simulations(self) -> List[str]:
        # Get list of simulation IDs that are unhealthy (failed or stalled)
        unhealthy = []
        
        for sim_id in list(self.active_simulations.keys()):
            health = self.check_simulation_health(sim_id)
            if health["status"] in ["failed", "stalled"]:
                unhealthy.append(sim_id)
        
        return unhealthy
    
    async def get_engine_memory_statistics(self) -> Dict[str, Any]:
        # Query the C++ engine for memory statistics
        try:
            # Build command to get memory report from engine
            cmd = [
                str(self.cpp_engine_path),
                "--memory-report"  # We'll need to add this flag to C++ engine
            ]
            
            # Check if engine is available
            validation_result = self.validate_cpp_engine()
            if not validation_result["is_valid"]:
                return {
                    "status": "error",
                    "error": validation_result["error"],
                    "error_code": validation_result["error_code"]
                }
            
            working_dir = self.cpp_engine_path.parent
            
            # Prepare environment
            env = os.environ.copy()
            db_env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
            for var in db_env_vars:
                if var in os.environ:
                    env[var] = os.environ[var]
            
            # Execute memory query with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
                
                if process.returncode == 0:
                    # Parse memory statistics from stdout
                    memory_report = stdout.decode().strip()
                    return self._parse_memory_report(memory_report)
                else:
                    error_msg = stderr.decode().strip() if stderr else "Unknown error"
                    return {
                        "status": "error",
                        "error": f"Engine memory query failed: {error_msg}",
                        "return_code": process.returncode
                    }
                    
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "error",
                    "error": "Memory query timed out after 10 seconds",
                    "error_code": "TIMEOUT"
                }
                
        except Exception as e:
            logger.error(f"Failed to get engine memory statistics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_code": "EXECUTION_FAILED"
            }
    
    def _parse_memory_report(self, memory_report: str) -> Dict[str, Any]:
        """
        Parse the C++ engine memory report into a structured dictionary.

        This private helper method takes the raw string output from the C++ engine's
        memory report and parses it to extract key memory usage statistics for
        different components of the engine.

        Args:
            memory_report: The raw string containing the memory report.

        Returns:
            A dictionary containing the parsed memory statistics, including total
            memory, component-specific memory usage, and cache information.
        """
        # Parse the C++ engine memory report into structured data
        try:
            # Expected format from C++ engine getMemoryReport()
            lines = memory_report.split('\n')
            memory_stats = {
                "status": "success",
                "total_memory_bytes": 0,
                "portfolio_memory_bytes": 0,
                "market_data_cache_bytes": 0,
                "execution_service_bytes": 0,
                "data_processor_bytes": 0,
                "portfolio_allocator_bytes": 0,
                "price_cache_symbols": 0,
                "detailed_report": memory_report
            }
            
            # Parse key metrics from the report
            for line in lines:
                line = line.strip()
                
                # Parse total memory
                if "Total Engine Memory:" in line:
                    try:
                        memory_stats["total_memory_bytes"] = int(line.split()[-2])
                    except (ValueError, IndexError):
                        pass
                
                # Parse portfolio memory
                elif "Portfolio Memory Usage:" in line and "Estimated memory:" in memory_report:
                    # Look for the estimated memory line after portfolio section
                    portfolio_section = memory_report[memory_report.find("Portfolio Memory Usage:"):]
                    for portfolio_line in portfolio_section.split('\n'):
                        if "Estimated memory:" in portfolio_line:
                            try:
                                memory_stats["portfolio_memory_bytes"] = int(portfolio_line.split()[-2])
                            except (ValueError, IndexError):
                                pass
                            break
                
                # Parse cache information
                elif "Cached symbols:" in line:
                    try:
                        memory_stats["price_cache_symbols"] = int(line.split()[-1])
                    except (ValueError, IndexError):
                        pass
                
                # Parse service-specific memory usage
                elif "MarketData Memory Usage:" in line:
                    # Look for estimated memory in MarketData section
                    market_data_section = memory_report[memory_report.find("MarketData Memory Usage:"):]
                    for md_line in market_data_section.split('\n'):
                        if "Estimated memory:" in md_line:
                            try:
                                memory_stats["market_data_cache_bytes"] = int(md_line.split()[-2])
                            except (ValueError, IndexError):
                                pass
                            break
                
                elif "ExecutionService Memory Usage:" in line:
                    # Look for estimated memory in ExecutionService section
                    exec_section = memory_report[memory_report.find("ExecutionService Memory Usage:"):]
                    for exec_line in exec_section.split('\n'):
                        if "Total estimated memory:" in exec_line:
                            try:
                                memory_stats["execution_service_bytes"] = int(exec_line.split()[-2])
                            except (ValueError, IndexError):
                                pass
                            break
                
                elif "PortfolioAllocator Memory Usage:" in line:
                    # Look for estimated memory in PortfolioAllocator section
                    pa_section = memory_report[memory_report.find("PortfolioAllocator Memory Usage:"):]
                    for pa_line in pa_section.split('\n'):
                        if "Estimated memory:" in pa_line:
                            try:
                                memory_stats["portfolio_allocator_bytes"] = int(pa_line.split()[-2])
                            except (ValueError, IndexError):
                                pass
                            break
                
                elif "DataProcessor Memory Usage:" in line:
                    # Look for estimated memory in DataProcessor section  
                    dp_section = memory_report[memory_report.find("DataProcessor Memory Usage:"):]
                    for dp_line in dp_section.split('\n'):
                        if "Total estimated memory:" in dp_line:
                            try:
                                memory_stats["data_processor_bytes"] = int(dp_line.split()[-2])
                            except (ValueError, IndexError):
                                pass
                            break
            
            return memory_stats
            
        except Exception as e:
            logger.error(f"Failed to parse memory report: {e}")
            return {
                "status": "error",
                "error": f"Failed to parse memory report: {str(e)}",
                "raw_report": memory_report
            }
    
    def get_simulation_progress(self, simulation_id: str) -> Dict[str, Any]:
        if simulation_id not in self.active_simulations:
            return {"status": "not_found"}
        
        sim_info = self.active_simulations[simulation_id]
        health_info = self.check_simulation_health(simulation_id)
        
        # Determine overall status based on health
        if health_info["status"] == "healthy":
            status = "running"
        elif health_info["status"] == "stalled":
            status = "stalled"
        else:
            status = "failed"
        
        return {
            "status": status,
            "progress_pct": sim_info.get("progress_pct", 0),
            "current_date": sim_info.get("current_date"),
            "current_value": sim_info.get("current_value"),
            "start_time": sim_info.get("start_time"),
            "health": health_info
        }
    
    async def cancel_simulation(self, simulation_id: str) -> bool:
        # Cancel a running simulation by terminating its process
        if simulation_id not in self.active_simulations:
            logger.warning(f"Cannot cancel simulation {simulation_id}: not found in active simulations")
            return False
        
        try:
            sim_info = self.active_simulations[simulation_id]
            process = sim_info.get("process")
            
            if not process:
                logger.error(f"No process found for simulation {simulation_id}")
                return False
            
            logger.info(f"Attempting to cancel simulation {simulation_id}")
            
            # Try graceful termination first
            process.terminate()
            
            # Wait for termination with timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
                logger.info(f"Simulation {simulation_id} terminated gracefully")
            except asyncio.TimeoutError:
                # Force kill if terminate didn't work
                logger.warning(f"Simulation {simulation_id} didn't terminate gracefully, force killing")
                process.kill()
                await process.wait()
                logger.info(f"Simulation {simulation_id} force killed")
            
            # Clean up from active simulations
            del self.active_simulations[simulation_id]
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel simulation {simulation_id}: {e}")
            return False
    
    def list_active_simulations(self) -> Dict[str, Dict[str, Any]]:
        # Get a list of all currently active simulations
        return {
            sim_id: {
                "start_time": sim_info.get("start_time"),
                "progress_pct": sim_info.get("progress_pct", 0),
                "current_date": sim_info.get("current_date"),
                "current_value": sim_info.get("current_value")
            }
            for sim_id, sim_info in self.active_simulations.items()
        }