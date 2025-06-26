import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from models import SimulationConfig, SimulationStatus
from performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)

class ExecutionService:
    def __init__(self, cpp_engine_path: Path):
        self.cpp_engine_path = cpp_engine_path
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
    
    def validate_cpp_engine(self) -> Dict[str, Any]:
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
        # Create a temporary JSON config file for the C++ engine
        config_data = {
            "symbol": config.symbols[0] if config.symbols else "AAPL",
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "starting_capital": config.starting_capital,
            "strategy": config.strategy.value if hasattr(config.strategy, 'value') else str(config.strategy),
            "cleanup": True
        }
        
        # Add strategy-specific parameters
        if config.strategy == "ma_crossover":
            config_data.update({
                "short_ma": config.short_ma or 20,
                "long_ma": config.long_ma or 50
            })
        elif config.strategy == "rsi":
            config_data.update({
                "rsi_period": config.rsi_period or 14,
                "rsi_oversold": config.rsi_oversold or 30.0,
                "rsi_overbought": config.rsi_overbought or 70.0
            })
        
        # Create temporary file
        config_file = f"/tmp/sim_config_{uuid.uuid4().hex[:8]}.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.debug(f"Created config file: {config_file}")
            return config_file
            
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            raise
    
    def build_cpp_command(self, config: SimulationConfig) -> tuple[List[str], str]:
        # Build command using JSON config file approach
        config_file = self.create_config_file(config)
        
        cmd = [
            str(self.cpp_engine_path),
            "--simulate",
            "--config", 
            config_file
        ]
        
        return cmd, config_file
    
    async def execute_simulation(self, simulation_id: str, config: SimulationConfig, 
                               optimization_info: Dict[str, Any] = None) -> Dict[str, Any]:
        config_file = None
        try:
            # Build command using JSON config file
            start_time = performance_optimizer.start_timer("command_building")
            cmd, config_file = self.build_cpp_command(config)
            
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
            
            # Store process for status tracking with heartbeat
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
            
            # Read output streams and handle progress updates
            stdout_data, stderr_data = await self._read_process_streams(process, simulation_id)
            
            # Wait for process completion
            await process.wait()
            
            # Combine the data
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
            # Clean up
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
            
            # Clean up config file if it wasn't cleaned up by C++ engine
            if config_file and os.path.exists(config_file):
                try:
                    os.remove(config_file)
                    logger.debug(f"Cleaned up config file: {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up config file {config_file}: {e}")
    
    async def _read_process_streams(self, process, simulation_id: str):
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