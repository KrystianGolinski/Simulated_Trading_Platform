# Simulation Engine - Core Orchestration Layer
# This module provides the central simulation orchestration system for the Trading Platform
# Key responsibilities:
# - Simulation lifecycle management (start, monitor, cancel, complete)
# - Integration with C++ trading engine for execution
# - Intelligent optimization through performance optimizer integration
# - Parallel and sequential execution coordination
# - Real-time progress tracking and status monitoring
# - Memory usage monitoring and optimization
# - Result aggregation and processing
# - Error handling and recovery mechanisms
#
# Architecture Integration:
# - Acts as the central coordinator between API layer and C++ engine
# - Integrates with PerformanceOptimizer for intelligent execution strategies
# - Uses ExecutionService for C++ engine communication
# - Employs ResultProcessor for output parsing and validation
# - Provides unified interface for both sequential and parallel simulations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models import SimulationConfig, SimulationResults, SimulationStatus
from performance_optimizer import performance_optimizer
from services.error_handler import ErrorHandler
from services.execution_service import ExecutionService
from services.result_processor import ResultProcessor

logger = logging.getLogger(__name__)


class SimulationEngine:
    # Central simulation orchestration engine
    # Coordinates all aspects of simulation execution from API requests to result delivery
    # Integrates multiple specialized services for optimal performance and reliability

    def __init__(self):
        # C++ trading engine integration via Docker shared volume
        # The engine executable is mounted at /shared/trading_engine in the container
        self.cpp_engine_path = Path("/shared/trading_engine")
        logger.info(f"Using shared C++ engine path: {self.cpp_engine_path}")

        # Initialize specialized service components using dependency injection pattern
        self.execution_service = ExecutionService(
            self.cpp_engine_path
        )  # C++ engine communication
        self.result_processor = ResultProcessor()  # Result parsing and validation
        self.error_handler = ErrorHandler()  # Structured error handling

        # Parallel execution tracking and coordination
        # Maps main simulation IDs to their parallel execution metadata
        # Structure: main_sim_id -> {group_ids: [...], optimization_info: {...}, status: ...}
        self.parallel_executions = {}  # Active parallel simulation tracking

    def _validate_cpp_engine(self) -> Dict[str, Any]:
        # Validate C++ trading engine availability and functionality
        # Delegates to ExecutionService for comprehensive engine validation
        return self.execution_service.validate_cpp_engine()

    async def start_simulation(self, config: SimulationConfig) -> str:
        # Start a new simulation with intelligent optimization and return unique simulation ID
        # This method initiates the complete simulation lifecycle including:
        # - Engine validation and readiness checks
        # - Performance optimization analysis
        # - Background execution with progress tracking
        # - Result processing and storage coordination

        # Comprehensive engine validation before simulation start
        engine_validation = self._validate_cpp_engine()
        if not engine_validation["is_valid"]:
            raise RuntimeError(
                f"C++ trading engine validation failed: {engine_validation['error']}"
            )

        # Generate unique simulation identifier for tracking and correlation
        simulation_id = str(uuid.uuid4())

        # Initialize simulation result storage and metadata
        # Creates initial result structure for progress tracking
        self.result_processor.initialize_simulation_result(simulation_id, config)

        # Perform intelligent optimization analysis to determine execution strategy
        # Analyzes complexity and determines sequential vs parallel execution
        optimization_info = await performance_optimizer.optimize_simulation_execution(
            config
        )
        logger.info(
            f"Simulation {simulation_id} optimization strategy: {optimization_info['strategy_name']} "
            f"({optimization_info['execution_mode']}) - estimated speedup: {optimization_info.get('estimated_speedup', 1.0)}x"
        )

        # Start simulation execution in background to avoid blocking API response
        # Uses asyncio.create_task for proper async execution without blocking
        asyncio.create_task(
            self._run_simulation(simulation_id, config, optimization_info)
        )

        return simulation_id

    async def _run_simulation(
        self,
        simulation_id: str,
        config: SimulationConfig,
        optimization_info: Dict[str, Any] = None,
    ):
        # Core simulation execution workflow with comprehensive monitoring and error handling
        # Handles both sequential and parallel execution modes with real-time progress tracking
        # Integrates memory monitoring, result processing, and optimization analytics
        try:
            # Log optimization strategy selection for monitoring and debugging
            if optimization_info:
                strategy_name = optimization_info.get("strategy_name", "unknown")
                execution_mode = optimization_info.get("execution_mode", "unknown")
                estimated_speedup = optimization_info.get("estimated_speedup", 1.0)
                complexity_score = optimization_info.get("complexity_score", "unknown")

                logger.info(
                    f"Simulation {simulation_id} executing with strategy: {strategy_name}"
                )
                logger.info(
                    f"Execution mode: {execution_mode}, Expected speedup: {estimated_speedup}x, "
                    f"Complexity score: {complexity_score}"
                )

            # Capture baseline memory statistics for optimization analysis
            # Enables memory usage tracking and optimization recommendations
            baseline_memory = await self._capture_memory_statistics("baseline")
            memory_timeline = [baseline_memory] if baseline_memory else []

            # Update simulation status to running with timestamp
            # Enables real-time status monitoring via API endpoints
            self.result_processor.update_simulation_status(
                simulation_id, SimulationStatus.RUNNING, datetime.now()
            )

            # Execute simulation using optimizer-determined strategy (parallel or sequential)
            if (
                optimization_info
                and optimization_info.get("execution_mode") == "parallel"
            ):
                # Parallel execution path for complex simulations with multiple symbol groups
                symbol_groups = optimization_info.get("symbol_groups", [])
                parallel_tasks = optimization_info.get("parallel_tasks", 0)

                logger.info(
                    f"Executing parallel simulation with {len(symbol_groups)} groups, "
                    f"{parallel_tasks} parallel tasks, estimated efficiency: "
                    f"{optimization_info.get('estimated_efficiency', 'unknown')}"
                )

                # Pre-generate unique group IDs for immediate progress tracking
                # Enables real-time progress monitoring before execution starts
                group_ids = [
                    f"group_{i}_{str(uuid.uuid4())[:8]}"
                    for i in range(len(symbol_groups))
                ]

                # Store comprehensive parallel execution metadata for progress tracking
                # This metadata enables real-time progress aggregation across all groups
                self.parallel_executions[simulation_id] = {
                    "group_ids": group_ids,  # Pre-generated unique identifiers
                    "optimization_info": optimization_info,  # Optimization strategy and metrics
                    "symbol_groups": symbol_groups,  # Symbol distribution across groups
                    "status": "running",  # Current execution status
                    "total_groups": len(
                        symbol_groups
                    ),  # Total number of parallel groups
                    "start_time": datetime.now(),  # Execution start timestamp
                }

                logger.info(
                    f"Stored parallel execution metadata for {simulation_id}: {len(group_ids)} groups "
                    f"with optimization strategy '{optimization_info.get('strategy_name')}'"
                )

                # Execute parallel simulation groups with comprehensive tracking
                # Coordinates execution across multiple groups while maintaining progress visibility
                group_results = await self._execute_parallel_with_tracking(
                    simulation_id, symbol_groups, config, optimization_info, group_ids
                )

                # Aggregate results from all parallel groups into unified simulation result
                # Combines performance metrics, trade data, and execution metadata
                aggregated_result = await self._aggregate_parallel_results(
                    simulation_id, group_results, optimization_info
                )

                # Process aggregated parallel execution results with comprehensive analysis
                if aggregated_result["status"] == "success":
                    # Capture final memory statistics for optimization analysis
                    final_memory = await self._capture_memory_statistics("final")
                    if final_memory:
                        memory_timeline.append(final_memory)

                    # Enhance result data with memory optimization insights
                    if memory_timeline:
                        aggregated_result["data"]["memory_statistics"] = (
                            self._create_memory_summary(
                                memory_timeline, optimization_info
                            )
                        )

                    # Process successful parallel execution results
                    self.result_processor.process_simulation_results(
                        simulation_id, aggregated_result["data"]
                    )

                    logger.info(
                        f"Parallel simulation {simulation_id} completed successfully with "
                        f"{len(group_results)} groups, actual speedup: "
                        f"{aggregated_result['data'].get('optimization_info', {}).get('actual_speedup', 'unknown')}x"
                    )
                else:
                    # Handle parallel execution failure with detailed error information
                    error_msg = aggregated_result["error"]
                    failed_groups = aggregated_result.get("failed_groups", [])

                    self.result_processor.mark_simulation_failed(
                        simulation_id, error_msg
                    )
                    logger.error(
                        f"Parallel simulation {simulation_id} failed: {error_msg}, "
                        f"failed groups: {len(failed_groups)}"
                    )

                # Clean up parallel execution tracking to prevent memory leaks
                if simulation_id in self.parallel_executions:
                    del self.parallel_executions[simulation_id]
                    logger.debug(
                        f"Cleaned up parallel execution metadata for {simulation_id}"
                    )

            else:
                # Sequential execution path for simple simulations or optimizer-recommended sequential mode
                logger.info(
                    f"Executing sequential simulation (reason: {optimization_info.get('reasoning', 'optimizer recommendation') if optimization_info else 'default mode'})"
                )

                # Execute simulation directly using execution service
                # Single-threaded execution with full resource dedication
                execution_result = await self.execution_service.execute_simulation(
                    simulation_id, config
                )

                # Process sequential execution results with comprehensive validation and enhancement
                if execution_result["return_code"] == 0:
                    try:
                        # Parse and validate JSON results from C++ engine
                        result_data = self.result_processor.parse_json_result(
                            execution_result["stdout"]
                        )

                        if self.result_processor.validate_result_data(result_data):
                            # Capture final memory statistics for optimization analysis
                            final_memory = await self._capture_memory_statistics(
                                "final"
                            )
                            if final_memory:
                                memory_timeline.append(final_memory)

                            # Enhance result data with optimization metadata for performance analysis
                            if optimization_info:
                                result_data["optimization_info"] = {
                                    "strategy_used": optimization_info.get(
                                        "strategy_name"
                                    ),
                                    "execution_mode": optimization_info.get(
                                        "execution_mode"
                                    ),
                                    "complexity_score": optimization_info.get(
                                        "complexity_score"
                                    ),
                                    "estimated_speedup": optimization_info.get(
                                        "estimated_speedup"
                                    ),
                                    "actual_speedup": 1.0,  # Sequential execution baseline
                                    "optimization_time_ms": optimization_info.get(
                                        "optimization_time_ms"
                                    ),
                                    "reasoning": optimization_info.get("reasoning"),
                                }

                            # Add comprehensive memory tracking and analysis
                            if memory_timeline:
                                result_data["memory_statistics"] = (
                                    self._create_memory_summary(
                                        memory_timeline, optimization_info
                                    )
                                )

                            # Process successful sequential execution results
                            self.result_processor.process_simulation_results(
                                simulation_id, result_data
                            )
                            logger.info(
                                f"Sequential simulation {simulation_id} completed successfully"
                            )
                        else:
                            # Handle result validation failure with detailed error context
                            error = self.error_handler.create_validation_error(
                                "Invalid result data structure from C++ engine",
                                {
                                    "stdout_preview": execution_result["stdout"][:200],
                                    "simulation_id": simulation_id,
                                    "execution_mode": "sequential",
                                },
                            )
                            self.result_processor.mark_simulation_failed(
                                simulation_id, error.message
                            )
                            logger.error(
                                f"Result validation failed for simulation {simulation_id}: {error.message}"
                            )

                    except json.JSONDecodeError as e:
                        # Handle JSON parsing errors with structured error information
                        error = self.error_handler.create_json_parse_error(
                            str(e), execution_result["stdout"]
                        )
                        self.result_processor.mark_simulation_failed(
                            simulation_id, error.message
                        )
                        logger.error(
                            f"JSON parsing failed for simulation {simulation_id}: {str(e)}"
                        )

                else:
                    # Handle C++ engine execution failure with categorized error analysis
                    error = self.error_handler.categorize_cpp_engine_error(
                        execution_result["return_code"],
                        execution_result["stdout"],
                        execution_result["stderr"],
                    )
                    self.result_processor.mark_simulation_failed(
                        simulation_id, error.message
                    )
                    logger.error(
                        f"C++ engine execution failed for simulation {simulation_id}: "
                        f"return code {execution_result['return_code']}, error: {error.message}"
                    )

        except Exception as e:
            # Handle unexpected errors during simulation execution with comprehensive context
            error = self.error_handler.create_generic_error(
                f"Unexpected error in simulation {simulation_id}: {str(e)}",
                {
                    "simulation_id": simulation_id,
                    "execution_mode": (
                        optimization_info.get("execution_mode", "unknown")
                        if optimization_info
                        else "unknown"
                    ),
                    "strategy_name": (
                        optimization_info.get("strategy_name", "unknown")
                        if optimization_info
                        else "unknown"
                    ),
                    "exception_type": type(e).__name__,
                    "error_context": "simulation_execution",
                },
            )
            self.result_processor.mark_simulation_failed(simulation_id, error.message)
            logger.error(
                f"Unexpected simulation error for {simulation_id}: {str(e)}",
                exc_info=True,
            )

    async def _execute_parallel_with_tracking(
        self,
        simulation_id: str,
        symbol_groups: List[List[str]],
        config: SimulationConfig,
        optimization_info: Dict[str, Any],
        group_ids: List[str],
    ) -> List[Dict[str, Any]]:
        # Execute parallel simulation with comprehensive progress tracking and group coordination
        # Coordinates execution across multiple symbol groups while maintaining real-time visibility
        # Integrates with PerformanceOptimizer for optimal parallel execution management
        from performance_optimizer import performance_optimizer

        logger.info(
            f"Starting parallel execution for {simulation_id} with {len(symbol_groups)} groups"
        )

        # Execute parallel groups using performance optimizer with pre-assigned group IDs
        # This enables immediate progress tracking and result correlation
        group_results = await performance_optimizer.execute_simulation_groups(
            symbol_groups, config, group_ids, self.execution_service
        )

        # Verify group ID consistency for progress tracking integrity
        actual_group_ids = [
            result.get("simulation_id")
            for result in group_results
            if result.get("simulation_id")
        ]

        if len(actual_group_ids) != len(group_ids):
            logger.warning(
                f"Group ID mismatch for {simulation_id}: expected {len(group_ids)}, "
                f"got {len(actual_group_ids)}. This may affect progress tracking accuracy."
            )
            # Update tracking metadata with actual group IDs to maintain consistency
            if simulation_id in self.parallel_executions:
                self.parallel_executions[simulation_id]["group_ids"] = actual_group_ids
                logger.debug(
                    f"Updated group IDs for {simulation_id} to maintain tracking consistency"
                )

        # Log execution results summary for monitoring
        successful_groups = [r for r in group_results if r.get("status") == "completed"]
        failed_groups = [r for r in group_results if r.get("status") == "failed"]

        logger.info(
            f"Parallel execution completed for {simulation_id}: {len(successful_groups)} successful, "
            f"{len(failed_groups)} failed out of {len(group_results)} total groups"
        )

        return group_results

    async def _aggregate_parallel_results(
        self, simulation_id: str, group_results: list, optimization_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Aggregate results from parallel group executions
        try:
            successful_groups = []
            failed_groups = []

            logger.info(
                f"Aggregating results for simulation {simulation_id}: {len(group_results)} groups"
            )

            # Separate successful and failed groups
            for result in group_results:
                logger.info(
                    f"Group {result.get('group_id')}: status={result.get('status')}"
                )
                if result.get("status") == "completed":
                    successful_groups.append(result)
                    logger.info(
                        f"Group {result.get('group_id')} data keys: {list(result.get('result_data', {}).keys())}"
                    )
                else:
                    failed_groups.append(result)

            # If any groups failed, return failure
            if failed_groups:
                failed_count = len(failed_groups)
                total_count = len(group_results)
                error_details = []

                for failed_group in failed_groups:
                    error_details.append(
                        {
                            "group_id": failed_group.get("group_id"),
                            "symbols": failed_group.get("symbols", []),
                            "error": failed_group.get("error", "Unknown error"),
                        }
                    )

                logger.warning(
                    f"Parallel execution partially failed: {failed_count}/{total_count} groups failed"
                )
                return {
                    "status": "failed",
                    "error": f"Parallel execution failed: {failed_count}/{total_count} groups failed",
                    "failed_groups": error_details,
                }

            # All groups succeeded - aggregate their results
            if not successful_groups:
                logger.error("No successful groups to aggregate")
                return {
                    "status": "failed",
                    "error": "No successful groups to aggregate",
                }

            # Initialize aggregated data structure with minimal fields (don't pre-populate with zeros)
            aggregated_data = {
                "trade_log": [],
                "daily_balance": {},
                "symbols_processed": [],
                "parallel_execution_info": {
                    "groups_executed": len(successful_groups),
                    "total_execution_time_ms": sum(
                        g.get("execution_time_ms", 0) for g in successful_groups
                    ),
                    "parallel_speedup_achieved": optimization_info.get(
                        "estimated_speedup", 1.0
                    ),
                    "strategy_used": optimization_info.get("strategy_name", "unknown"),
                },
            }

            # Simple pass-through aggregation: combine trade logs and directly use C++ engine results
            # Use the first group's results as the base and combine trade data from all groups
            base_result = successful_groups[0].get("result_data", {})

            # Start with the base result (C++ engine calculated metrics)
            for key, value in base_result.items():
                if key not in [
                    "trade_log",
                    "daily_balance",
                ]:  # Don't overwrite these, we'll aggregate them
                    aggregated_data[key] = value
                    logger.debug(f"Copied {key}: {value}")

            # Collect symbols from all groups
            for group_result in successful_groups:
                group_symbols = group_result.get("symbols", [])
                aggregated_data["symbols_processed"].extend(group_symbols)

            # Combine trade logs from all groups
            for group_result in successful_groups:
                result_data = group_result.get("result_data", {})
                if "trade_log" in result_data:
                    aggregated_data["trade_log"].extend(result_data["trade_log"])

            # Implement proper portfolio-level daily balance aggregation
            # Aggregate daily balances from all parallel groups by date
            daily_balance_combined = {}
            groups_with_balance = 0
            
            for group_result in successful_groups:
                result_data = group_result.get("result_data", {})
                if "daily_balance" in result_data and result_data["daily_balance"]:
                    groups_with_balance += 1
                    group_daily_balance = result_data["daily_balance"]
                    
                    # Validate that daily_balance is a dictionary
                    if not isinstance(group_daily_balance, dict):
                        logger.warning(
                            f"Group {group_result.get('group_id')} has invalid daily_balance format: "
                            f"{type(group_daily_balance)}, skipping"
                        )
                        continue
                    
                    # Aggregate balances by date
                    for date_str, balance in group_daily_balance.items():
                        if isinstance(balance, (int, float)):
                            if date_str in daily_balance_combined:
                                daily_balance_combined[date_str] += balance
                            else:
                                daily_balance_combined[date_str] = balance
                        else:
                            logger.warning(
                                f"Invalid balance value for date {date_str} in group "
                                f"{group_result.get('group_id')}: {balance} ({type(balance)})"
                            )
            
            # Set aggregated daily balance with additional validation
            aggregated_data["daily_balance"] = daily_balance_combined
            
            # Validate aggregated daily balance data consistency
            if daily_balance_combined:
                # Check for date format consistency and sort dates
                sorted_dates = sorted(daily_balance_combined.keys())
                date_count = len(sorted_dates)
                
                # Basic date format validation (YYYY-MM-DD expected)
                invalid_dates = []
                for date_str in sorted_dates[:5]:  # Check first 5 dates for performance
                    if not isinstance(date_str, str) or len(date_str) != 10 or date_str.count('-') != 2:
                        invalid_dates.append(date_str)
                
                if invalid_dates:
                    logger.warning(
                        f"Found {len(invalid_dates)} dates with potentially invalid format: {invalid_dates[:3]}..."
                    )
                
                # Check for reasonable balance values
                balance_values = list(daily_balance_combined.values())
                min_balance = min(balance_values)
                max_balance = max(balance_values)
                
                if min_balance < 0:
                    logger.warning(f"Aggregated daily balance contains negative values: min={min_balance}")
                
                # Validate aggregated balances against individual group balances for consistency
                # Check if aggregated final balance is reasonable compared to individual group final balances
                if groups_with_balance > 1:
                    individual_final_balances = []
                    for group_result in successful_groups:
                        result_data = group_result.get("result_data", {})
                        if "daily_balance" in result_data and result_data["daily_balance"]:
                            group_daily_balance = result_data["daily_balance"]
                            if isinstance(group_daily_balance, dict) and group_daily_balance:
                                # Get the final balance (last date) from this group
                                group_sorted_dates = sorted(group_daily_balance.keys())
                                if group_sorted_dates:
                                    final_balance = group_daily_balance[group_sorted_dates[-1]]
                                    if isinstance(final_balance, (int, float)):
                                        individual_final_balances.append(final_balance)
                    
                    if individual_final_balances and len(individual_final_balances) == groups_with_balance:
                        sum_individual_final = sum(individual_final_balances)
                        aggregated_final = max_balance  # Assuming max_balance is the final balance
                        
                        # Allow for small floating point discrepancies (within 0.01%)
                        tolerance = max(abs(sum_individual_final) * 0.0001, 0.01)
                        if abs(aggregated_final - sum_individual_final) > tolerance:
                            logger.warning(
                                f"Balance validation warning: aggregated final balance (${aggregated_final:,.2f}) "
                                f"differs from sum of individual final balances (${sum_individual_final:,.2f}) "
                                f"by ${abs(aggregated_final - sum_individual_final):,.2f}"
                            )
                        else:
                            logger.debug(
                                f"Balance validation passed: aggregated final balance matches sum of individual balances "
                                f"within tolerance (${aggregated_final:,.2f} vs ${sum_individual_final:,.2f})"
                            )
                
                logger.info(
                    f"Aggregated daily balances from {groups_with_balance}/{len(successful_groups)} groups, "
                    f"covering {date_count} trading days (dates: {sorted_dates[0]} to {sorted_dates[-1]}), "
                    f"balance range: ${min_balance:,.2f} to ${max_balance:,.2f}"
                )
            else:
                logger.warning("No daily balance data available from any parallel groups")
                # Ensure we have an empty dict rather than None for consistency
                aggregated_data["daily_balance"] = {}

            # Ensure all expected field names are present for result processor
            # Only set ending_value from final_balance if final_balance has a valid value
            # and ending_value doesn't already exist or is zero
            if (
                "final_balance" in aggregated_data
                and aggregated_data["final_balance"]
                and aggregated_data["final_balance"] != 0.0
                and (
                    not aggregated_data.get("ending_value")
                    or aggregated_data.get("ending_value") == 0.0
                )
            ):
                aggregated_data["ending_value"] = aggregated_data["final_balance"]

            # Conversely, if ending_value exists but final_balance doesn't, use ending_value for final_balance
            elif (
                "ending_value" in aggregated_data
                and aggregated_data["ending_value"]
                and aggregated_data["ending_value"] != 0.0
                and (
                    not aggregated_data.get("final_balance")
                    or aggregated_data.get("final_balance") == 0.0
                )
            ):
                aggregated_data["final_balance"] = aggregated_data["ending_value"]

            # Map other field name variations that result processor expects
            if (
                "starting_capital" not in aggregated_data
                and "initial_capital" in aggregated_data
            ):
                aggregated_data["starting_capital"] = aggregated_data["initial_capital"]

            # Sort trade log by date if present
            if aggregated_data["trade_log"]:
                aggregated_data["trade_log"].sort(
                    key=lambda x: x.get("date", "") if isinstance(x, dict) else ""
                )

            # Calculate actual speedup based on execution times
            sequential_time_ms = sum(
                g.get("execution_time_ms", 0) for g in successful_groups
            )
            parallel_time_ms = (
                max(g.get("execution_time_ms", 0) for g in successful_groups)
                if successful_groups
                else 1
            )
            actual_speedup = (
                sequential_time_ms / parallel_time_ms if parallel_time_ms > 0 else 1.0
            )

            # Add optimization information
            aggregated_data["optimization_info"] = {
                "strategy_used": optimization_info.get("strategy_name"),
                "execution_mode": optimization_info.get("execution_mode"),
                "complexity_score": optimization_info.get("complexity_score"),
                "estimated_speedup": optimization_info.get("estimated_speedup"),
                "actual_speedup": round(actual_speedup, 2),
                "optimization_time_ms": optimization_info.get("optimization_time_ms"),
                "parallel_efficiency": optimization_info.get("estimated_efficiency"),
                "timing_analysis": {
                    "sequential_time_ms": sequential_time_ms,
                    "parallel_time_ms": parallel_time_ms,
                    "speedup_achieved": round(actual_speedup, 2),
                },
            }

            logger.info(
                f"Successfully aggregated {len(successful_groups)} parallel groups for simulation {simulation_id}"
            )
            return {"status": "success", "data": aggregated_data}

        except Exception as e:
            logger.error(
                f"Failed to aggregate parallel results for simulation {simulation_id}: {e}"
            )
            return {"status": "failed", "error": f"Result aggregation failed: {str(e)}"}

    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationResults]:
        # Retrieve current status and metadata for a simulation
        # Returns complete simulation results including progress, performance metrics, and metadata
        return self.result_processor.get_simulation_result(simulation_id)

    def get_simulation_progress(self, simulation_id: str) -> Dict[str, Any]:
        # Get real-time simulation progress with intelligent routing for parallel vs sequential simulations
        # Automatically detects execution mode and provides appropriate progress aggregation

        # Check if this is an active parallel simulation
        if simulation_id in self.parallel_executions:
            # Parallel simulation - aggregate progress from all groups
            parallel_info = self.parallel_executions[simulation_id]
            group_ids = parallel_info["group_ids"]

            logger.debug(
                f"Retrieving parallel progress for {simulation_id} with {len(group_ids)} groups"
            )
            return self._aggregate_parallel_progress(simulation_id, group_ids)
        else:
            # Sequential simulation - delegate directly to execution service
            logger.debug(f"Retrieving sequential progress for {simulation_id}")
            return self.execution_service.get_simulation_progress(simulation_id)

    def _aggregate_parallel_progress(
        self, main_simulation_id: str, group_ids: List[str]
    ) -> Dict[str, Any]:
        # Aggregate progress from all parallel groups using stored group IDs
        parallel_info = self.parallel_executions.get(main_simulation_id, {})
        total_groups = parallel_info.get("total_groups", len(group_ids))

        # Handle startup phase when group_ids is empty (should not happen with pre-generated IDs)
        if not group_ids:
            logger.warning(
                f"No group IDs available for parallel simulation {main_simulation_id}"
            )
            return {
                "status": "running",
                "progress_pct": 0.0,
                "current_date": None,
                "elapsed_time": None,
                "estimated_remaining": None,
            }

        total_progress = 0.0
        active_groups = 0
        completed_groups = 0
        failed_groups = 0
        not_started_groups = 0

        group_progress_details = []

        for group_id in group_ids:
            try:
                group_progress = self.execution_service.get_simulation_progress(
                    group_id
                )

                group_status = group_progress.get("status")
                group_pct = group_progress.get("progress_pct", 0.0)

                # Query individual group progress for aggregation

                if group_status == "not_found":
                    # Group might not have started yet or completed and been cleaned up
                    # If other groups have progress, assume this one completed
                    if any(
                        g.get("progress_pct", 0) > 0 for g in group_progress_details
                    ):
                        completed_groups += 1
                        total_progress += 100.0
                    else:
                        # Probably hasn't started yet
                        not_started_groups += 1

                elif group_status in ["running", "healthy"]:
                    # Active group
                    active_groups += 1
                    total_progress += group_pct
                    group_progress_details.append(
                        {
                            "group_id": group_id,
                            "progress_pct": group_pct,
                            "status": group_status,
                        }
                    )

                elif group_status in ["failed", "stalled"]:
                    if group_pct > 0:
                        # Failed group with some progress - still counts towards total
                        failed_groups += 1
                        total_progress += group_pct
                        group_progress_details.append(
                            {
                                "group_id": group_id,
                                "progress_pct": group_pct,
                                "status": group_status,
                            }
                        )
                    else:
                        # Failed group with no progress
                        failed_groups += 1
                        group_progress_details.append(
                            {
                                "group_id": group_id,
                                "progress_pct": 0.0,
                                "status": group_status,
                            }
                        )

                elif group_pct >= 100.0:
                    # Completed (100% progress regardless of status)
                    completed_groups += 1
                    total_progress += 100.0

                else:
                    # Unknown status but has progress - treat as active
                    active_groups += 1
                    total_progress += group_pct
                    group_progress_details.append(
                        {
                            "group_id": group_id,
                            "progress_pct": group_pct,
                            "status": group_status or "unknown",
                        }
                    )

            except Exception as e:
                logger.error(f"Error getting progress for group {group_id}: {e}")
                failed_groups += 1

        # Calculate overall progress with proper weighting
        overall_progress = total_progress / total_groups if total_groups > 0 else 0.0

        # Determine overall status with more nuanced logic
        if failed_groups > 0 and (completed_groups + active_groups) == 0:
            overall_status = "failed"
        elif completed_groups == total_groups:
            overall_status = "completed"
        elif active_groups > 0 or not_started_groups > 0:
            overall_status = "running"
        elif failed_groups > 0:
            overall_status = "failed"
        else:
            overall_status = "unknown"

        # Return format compatible with SimulationStatusResponse model
        result = {
            "status": overall_status,
            "progress_pct": round(overall_progress, 1),
            "current_date": None,  # Could extract from most recent group if needed
            "elapsed_time": None,  # Could calculate if needed
            "estimated_remaining": None,  # Could estimate based on progress if needed
        }

        # Log aggregated progress summary
        logger.debug(
            f"Parallel progress for {main_simulation_id}: {overall_progress:.1f}% ({overall_status})"
        )

        return result

    def list_simulations(self) -> Dict[str, SimulationResults]:
        # Retrieve all simulation results for monitoring and analysis
        # Returns comprehensive simulation history with performance metrics and status information
        return self.result_processor.get_all_simulation_results()

    async def cancel_simulation(self, simulation_id: str) -> bool:
        # Cancel a running simulation with support for both sequential and parallel execution modes
        # Handles graceful shutdown and cleanup of resources for all execution types
        try:
            logger.info(f"Attempting to cancel simulation {simulation_id}")

            # Check if this is a parallel simulation requiring group-level cancellation
            if simulation_id in self.parallel_executions:
                logger.info(
                    f"Cancelling parallel simulation {simulation_id} with multiple groups"
                )

                # For parallel simulations, we should ideally cancel all group processes
                # Currently delegating to execution service which handles the main process
                # Future enhancement: implement individual group cancellation

            # Attempt to cancel the running process via execution service
            cancelled = await self.execution_service.cancel_simulation(simulation_id)

            if cancelled:
                # Successfully cancelled - mark as failed with cancellation reason
                self.result_processor.mark_simulation_failed(
                    simulation_id, "Simulation cancelled by user"
                )

                # Clean up parallel execution tracking if applicable
                if simulation_id in self.parallel_executions:
                    del self.parallel_executions[simulation_id]
                    logger.debug(
                        f"Cleaned up parallel execution metadata for cancelled simulation {simulation_id}"
                    )

                logger.info(f"Simulation {simulation_id} successfully cancelled")
                return True
            else:
                # Process not found or already completed - mark as cancelled anyway
                self.result_processor.mark_simulation_failed(
                    simulation_id, "Simulation cancellation requested"
                )
                logger.info(
                    f"Simulation {simulation_id} marked as cancelled (process not active)"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to cancel simulation {simulation_id}: {e}")
            return False

    async def _capture_memory_statistics(self, phase: str) -> Optional[Dict[str, Any]]:
        """
        Capture memory statistics from the C++ engine at a specific phase of simulation.

        Args:
            phase: The simulation phase ('baseline', 'mid-execution', 'final')

        Returns:
            Dict containing memory statistics with timestamp, or None if capture failed
        """
        try:
            # Get memory statistics using the execution service
            memory_stats = await self.execution_service.get_engine_memory_statistics()

            if memory_stats.get("status") == "success":
                # Add phase and timestamp information
                memory_capture = {
                    "phase": phase,
                    "timestamp": datetime.now().isoformat(),
                    "memory_data": memory_stats,
                }

                logger.debug(
                    f"Captured memory statistics for phase '{phase}': "
                    f"{memory_stats.get('total_memory_bytes', 0)} bytes"
                )
                return memory_capture
            else:
                logger.warning(
                    f"Failed to capture memory statistics for phase '{phase}': "
                    f"{memory_stats.get('error', 'Unknown error')}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Exception while capturing memory statistics for phase '{phase}': {e}"
            )
            return None

    def _create_memory_summary(
        self,
        memory_timeline: List[Dict[str, Any]],
        optimization_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive memory summary from the captured timeline data.

        Args:
            memory_timeline: List of memory captures at different phases
            optimization_info: Optimization metadata from the simulation

        Returns:
            Dict containing memory summary with analysis and insights
        """
        try:
            if not memory_timeline:
                return {
                    "status": "no_data",
                    "message": "No memory data captured during simulation",
                }

            # Extract memory data from timeline
            baseline_data = None
            final_data = None

            for capture in memory_timeline:
                if capture["phase"] == "baseline":
                    baseline_data = capture["memory_data"]
                elif capture["phase"] == "final":
                    final_data = capture["memory_data"]

            # Create summary structure
            memory_summary = {
                "status": "success",
                "timeline": memory_timeline,
                "analysis": {
                    "phases_captured": len(memory_timeline),
                    "capture_phases": [capture["phase"] for capture in memory_timeline],
                },
            }

            # Add memory change analysis if we have baseline and final data
            if baseline_data and final_data:
                baseline_memory = baseline_data.get("total_memory_bytes", 0)
                final_memory = final_data.get("total_memory_bytes", 0)
                memory_change = final_memory - baseline_memory

                memory_summary["analysis"].update(
                    {
                        "baseline_memory_bytes": baseline_memory,
                        "final_memory_bytes": final_memory,
                        "memory_change_bytes": memory_change,
                        "memory_change_percent": round(
                            (
                                (memory_change / baseline_memory * 100)
                                if baseline_memory > 0
                                else 0
                            ),
                            2,
                        ),
                        "peak_memory_bytes": final_memory,  # In future, track actual peak
                        "memory_efficiency": (
                            "good"
                            if memory_change < baseline_memory * 0.5
                            else "moderate"
                        ),
                    }
                )

                # Add service-specific memory analysis
                service_analysis = {}
                for service in [
                    "portfolio_memory_bytes",
                    "market_data_cache_bytes",
                    "execution_service_bytes",
                    "portfolio_allocator_bytes",
                ]:
                    if service in baseline_data and service in final_data:
                        baseline_val = baseline_data.get(service, 0)
                        final_val = final_data.get(service, 0)
                        change = final_val - baseline_val
                        service_analysis[service] = {
                            "baseline": baseline_val,
                            "final": final_val,
                            "change": change,
                            "change_percent": round(
                                (
                                    (change / baseline_val * 100)
                                    if baseline_val > 0
                                    else 0
                                ),
                                2,
                            ),
                        }

                memory_summary["service_analysis"] = service_analysis

            # Add optimization correlation if available
            if optimization_info:
                memory_summary["optimization_correlation"] = {
                    "execution_mode": optimization_info.get("execution_mode"),
                    "complexity_score": optimization_info.get("complexity_score"),
                    "estimated_memory_mb": optimization_info.get("memory_estimate_mb"),
                    "parallel_tasks": optimization_info.get("parallel_tasks", 0),
                }

            # Add metadata
            memory_summary["metadata"] = {
                "captured_at": datetime.now().isoformat(),
                "engine_version": "1.0.0",
                "tracking_enabled": True,
            }

            logger.info(f"Created memory summary with {len(memory_timeline)} captures")
            return memory_summary

        except Exception as e:
            logger.error(f"Failed to create memory summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timeline_count": len(memory_timeline) if memory_timeline else 0,
            }


# Global simulation engine instance
# Singleton pattern ensures consistent simulation state and resource management
# Used by simulation routers and background task coordination
simulation_engine = SimulationEngine()
