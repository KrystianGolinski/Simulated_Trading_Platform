# Performance Optimization Module
# Complete parallel processing implementation with intelligent strategy selection

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Any, Optional
import logging

from models import SimulationConfig

logger = logging.getLogger(__name__)

class ParallelExecutionStrategy:
    # Strategy decision engine for execution planning
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.strategy_history = {}  # Track strategy performance over time
        self.complexity_thresholds = {
            "low": 5000,
            "medium": 25000,
            "high": 100000
        }
        self.parallel_efficiency_baseline = 0.7  # Minimum efficiency threshold for parallel execution
        
    def analyze_simulation_complexity(self, config: SimulationConfig) -> Dict[str, Any]:
        # Analyze simulation complexity for strategy decisions
        from datetime import datetime
        
        symbols_count = len(config.symbols)
        
        # Calculate date range
        start_date = datetime.fromisoformat(config.start_date) if isinstance(config.start_date, str) else config.start_date
        end_date = datetime.fromisoformat(config.end_date) if isinstance(config.end_date, str) else config.end_date
        date_range_days = (end_date - start_date).days
        
        # Base complexity calculation
        base_complexity = symbols_count * date_range_days
        
        # Strategy complexity multiplier
        strategy_multiplier = self._get_strategy_complexity_multiplier(config)
        
        # Market data complexity (more volatile periods require more computation)
        market_complexity_multiplier = 1.0
        if date_range_days > 365:  # Long-term simulations
            market_complexity_multiplier = 1.2
        
        total_complexity = base_complexity * strategy_multiplier * market_complexity_multiplier
        
        # Determine complexity category
        if total_complexity < self.complexity_thresholds["low"]:
            complexity_category = "low"
        elif total_complexity < self.complexity_thresholds["medium"]:
            complexity_category = "medium"
        elif total_complexity < self.complexity_thresholds["high"]:
            complexity_category = "high"
        else:
            complexity_category = "extreme"
        
        return {
            "symbols_count": symbols_count,
            "date_range_days": date_range_days,
            "base_complexity": base_complexity,
            "strategy_multiplier": strategy_multiplier,
            "market_complexity_multiplier": market_complexity_multiplier,
            "total_complexity": total_complexity,
            "complexity_category": complexity_category,
            "estimated_data_points": symbols_count * date_range_days,
            "memory_intensity": self._classify_memory_intensity(total_complexity)
        }
    
    def determine_optimal_strategy(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Determine optimal execution strategy based on comprehensive analysis
        symbols_count = complexity_analysis["symbols_count"]
        complexity_category = complexity_analysis["complexity_category"]
        
        # Single symbol optimization
        if symbols_count == 1:
            return self._create_single_symbol_strategy()
        
        # Multi-symbol strategy selection
        if complexity_category == "low":
            return self._create_sequential_strategy(complexity_analysis)
        elif complexity_category == "medium":
            return self._create_moderate_parallel_strategy(complexity_analysis)
        elif complexity_category == "high":
            return self._create_aggressive_parallel_strategy(complexity_analysis)
        else:  # extreme
            return self._create_extreme_parallel_strategy(complexity_analysis)
    
    def create_symbol_groups(self, symbols: List[str], strategy_decision: Dict[str, Any]) -> List[List[str]]:
        # Create balanced symbol groups based on strategy decision
        if strategy_decision["execution_mode"] == "sequential":
            return [symbols]
        
        optimal_group_size = strategy_decision.get("optimal_group_size", len(symbols))
        
        # Create balanced groups
        groups = []
        for i in range(0, len(symbols), optimal_group_size):
            group = symbols[i:i + optimal_group_size]
            groups.append(group)
        
        # Balance group sizes to improve parallel efficiency
        if len(groups) > 1:
            groups = self._balance_group_sizes(groups)
        
        return groups
    
    def predict_performance_gain(self, complexity_analysis: Dict[str, Any], strategy_decision: Dict[str, Any]) -> Dict[str, Any]:
        # Predict performance gain with advanced modeling
        if strategy_decision["execution_mode"] == "sequential":
            return self._predict_sequential_performance(complexity_analysis)
        
        return self._predict_parallel_performance(complexity_analysis, strategy_decision)
    
    def _get_strategy_complexity_multiplier(self, config: SimulationConfig) -> float:
        # Calculate strategy complexity multiplier
        if not hasattr(config, 'strategy') or not config.strategy:
            return 1.0
        
        # Strategy complexity mapping
        strategy_complexity = {
            "buy_and_hold": 0.8,
            "ma_crossover": 1.0,
            "mean_reversion": 1.2,
            "momentum": 1.3,
            "pairs_trading": 1.5,
            "multi_factor": 1.8,
            "ml_predictor": 2.0,
            "portfolio_optimization": 2.5
        }
        
        return strategy_complexity.get(config.strategy, 1.0)
    
    def _classify_memory_intensity(self, complexity_score: float) -> str:
        # Classify memory intensity based on complexity
        if complexity_score < 10000:
            return "low"
        elif complexity_score < 50000:
            return "medium"
        elif complexity_score < 200000:
            return "high"
        else:
            return "extreme"
    
    def _create_single_symbol_strategy(self) -> Dict[str, Any]:
        # Strategy for single symbol simulations
        return {
            "strategy_name": "single_symbol_optimized",
            "execution_mode": "sequential",
            "parallel_tasks": 0,
            "recommended_workers": 1,
            "optimal_group_size": 1,
            "reasoning": "Single symbol simulations are optimally executed sequentially",
            "expected_bottleneck": "data_processing"
        }
    
    def _create_sequential_strategy(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Strategy for low complexity simulations
        return {
            "strategy_name": "sequential_cached",
            "execution_mode": "sequential",
            "parallel_tasks": 0,
            "recommended_workers": 1,
            "optimal_group_size": complexity_analysis["symbols_count"],
            "reasoning": "Low complexity simulations have minimal benefit from parallelization",
            "expected_bottleneck": "io_bound"
        }
    
    def _create_moderate_parallel_strategy(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Strategy for medium complexity simulations
        symbols_count = complexity_analysis["symbols_count"]
        optimal_workers = min(self.max_workers, max(2, symbols_count // 2))
        
        return {
            "strategy_name": "moderate_parallel",
            "execution_mode": "parallel",
            "parallel_tasks": optimal_workers,
            "recommended_workers": optimal_workers,
            "optimal_group_size": max(2, symbols_count // optimal_workers),
            "reasoning": "Medium complexity benefits from moderate parallelization",
            "expected_bottleneck": "computation_bound"
        }
    
    def _create_aggressive_parallel_strategy(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Strategy for high complexity simulations
        symbols_count = complexity_analysis["symbols_count"]
        optimal_workers = min(self.max_workers, symbols_count)
        
        return {
            "strategy_name": "aggressive_parallel",
            "execution_mode": "parallel",
            "parallel_tasks": optimal_workers,
            "recommended_workers": optimal_workers,
            "optimal_group_size": max(1, symbols_count // optimal_workers),
            "reasoning": "High complexity simulations require aggressive parallelization",
            "expected_bottleneck": "memory_bound"
        }
    
    def _create_extreme_parallel_strategy(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Strategy for extreme complexity simulations
        symbols_count = complexity_analysis["symbols_count"]
        optimal_workers = self.max_workers
        
        return {
            "strategy_name": "extreme_parallel",
            "execution_mode": "parallel",
            "parallel_tasks": optimal_workers,
            "recommended_workers": optimal_workers,
            "optimal_group_size": max(1, symbols_count // optimal_workers),
            "reasoning": "Extreme complexity requires maximum parallelization",
            "expected_bottleneck": "system_resources",
            "resource_warning": "May require significant system resources"
        }
    
    def _balance_group_sizes(self, groups: List[List[str]]) -> List[List[str]]:
        # Balance group sizes to improve parallel efficiency
        if len(groups) <= 1:
            return groups
        
        # Redistribute symbols to balance group sizes
        all_symbols = [symbol for group in groups for symbol in group]
        target_group_size = len(all_symbols) // len(groups)
        remainder = len(all_symbols) % len(groups)
        
        balanced_groups = []
        symbol_index = 0
        
        for i in range(len(groups)):
            group_size = target_group_size + (1 if i < remainder else 0)
            balanced_groups.append(all_symbols[symbol_index:symbol_index + group_size])
            symbol_index += group_size
        
        return balanced_groups
    
    def _predict_sequential_performance(self, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Predict sequential execution performance
        base_memory = complexity_analysis["symbols_count"] * 10
        
        return {
            "estimated_speedup": 1.0,
            "estimated_efficiency": 1.0,
            "memory_estimate_mb": base_memory,
            "bottleneck_prediction": "single_threaded_processing",
            "scaling_potential": "none"
        }
    
    def _predict_parallel_performance(self, complexity_analysis: Dict[str, Any], strategy_decision: Dict[str, Any]) -> Dict[str, Any]:
        # Predict parallel execution performance using advanced modeling
        parallel_tasks = strategy_decision.get("parallel_tasks", 1)
        
        # Advanced Amdahl's Law with overhead modeling
        parallel_fraction = self._estimate_parallel_fraction(complexity_analysis)
        overhead_factor = self._calculate_overhead_factor(parallel_tasks)
        
        # Theoretical speedup with overhead consideration
        theoretical_speedup = 1 / ((1 - parallel_fraction) + (parallel_fraction / parallel_tasks))
        estimated_speedup = max(1.0, theoretical_speedup - overhead_factor)
        
        # Efficiency calculation
        estimated_efficiency = estimated_speedup / parallel_tasks
        
        # Memory estimation with parallel overhead
        base_memory = complexity_analysis["symbols_count"] * 10
        memory_overhead = 0.3 * parallel_tasks  # 30% more memory per worker
        memory_estimate_mb = base_memory * (1 + memory_overhead)
        
        # Bottleneck prediction
        bottleneck = self._predict_bottleneck(parallel_tasks, complexity_analysis)
        
        return {
            "estimated_speedup": round(estimated_speedup, 2),
            "estimated_efficiency": round(estimated_efficiency, 2),
            "memory_estimate_mb": round(memory_estimate_mb, 2),
            "bottleneck_prediction": bottleneck,
            "scaling_potential": "good" if estimated_efficiency > self.parallel_efficiency_baseline else "limited"
        }
    
    def _estimate_parallel_fraction(self, complexity_analysis: Dict[str, Any]) -> float:
        # Estimate what fraction of the work can be parallelized
        complexity_category = complexity_analysis["complexity_category"]
        
        # More complex simulations have higher parallel potential
        parallel_fractions = {
            "low": 0.6,
            "medium": 0.75,
            "high": 0.85,
            "extreme": 0.9
        }
        
        return parallel_fractions.get(complexity_category, 0.75)
    
    def _calculate_overhead_factor(self, parallel_tasks: int) -> float:
        # Calculate overhead factor for parallel execution
        # Overhead increases with more workers due to coordination costs
        base_overhead = 0.05  # 5% base overhead
        scaling_overhead = 0.02 * (parallel_tasks - 1)  # 2% per additional worker
        
        return base_overhead + scaling_overhead
    
    def _predict_bottleneck(self, parallel_tasks: int, complexity_analysis: Dict[str, Any]) -> str:
        # Predict the likely bottleneck for parallel execution
        if parallel_tasks > 6:
            return "parallel_coordination"
        elif complexity_analysis["memory_intensity"] == "extreme":
            return "memory_bound"
        elif complexity_analysis["complexity_category"] == "high":
            return "computation_bound"
        else:
            return "io_bound"

class SimulationMetrics:
    # Comprehensive performance analytics with parallel execution tracking
    def __init__(self):
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Timing metrics
        self.query_time_ms = 0.0
        self.simulation_time_ms = 0.0
        self.optimization_time_ms = 0.0
        
        # Resource metrics
        self.memory_usage_mb = 0.0
        self.cpu_usage_percent = 0.0
        
        # Parallel execution metrics
        self.parallel_tasks = 0
        self.sequential_tasks = 0
        self.worker_utilization = 0.0
        self.parallel_speedup_achieved = 0.0
        self.parallel_efficiency = 0.0
        
        # Strategy metrics
        self.strategy_decisions = {}  # Track which strategies were chosen
        self.execution_mode_counts = {"sequential": 0, "parallel": 0}
        
        # Performance regression tracking
        self.baseline_performance = {}
        self.performance_regression_detected = False
        
        # Symbol grouping metrics
        self.symbol_groups_created = 0
        self.optimal_group_size = 0
        self.group_balance_score = 0.0

class PerformanceOptimizer:
    # Handles performance optimizations for trading simulations
    
    def __init__(self):
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour
        self.parallel_enabled = True
        self.max_workers = 4
        
        # Performance tracking
        self.metrics = SimulationMetrics()
        self.operation_times: Dict[str, List[float]] = {}
        
        # Strategy decision engine
        self.strategy_engine = ParallelExecutionStrategy(max_workers=self.max_workers)
        
        # Executors for parallel processing
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=min(4, self.max_workers))
        
        logger.info(f"Performance optimizer initialized with {self.max_workers} max workers")
    
    def start_timer(self, operation: str) -> float:
        # Start timing an operation
        return time.time()
    
    def end_timer(self, operation: str, start_time: float) -> float:
        # End timing and record the result
        duration = (time.time() - start_time) * 1000  # Convert to ms
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(duration)
        return duration
    
    async def optimize_simulation_execution(self, config: SimulationConfig) -> Dict[str, Any]:
        """
        Modern optimization with complexity analysis and intelligent strategy selection.
        
        Analyzes simulation configuration and determines optimal execution strategy including:
        - Complexity analysis based on symbols count, date range, and strategy type
        - Intelligent strategy selection (sequential vs parallel execution modes)
        - Symbol grouping for parallel execution optimization
        - Performance prediction using Amdahl's Law with overhead modeling
        
        Args:
            config (SimulationConfig): Simulation configuration containing symbols, 
                                     date range, strategy, and parameters
        
        Returns:
            Dict[str, Any]: Comprehensive optimization analysis containing:
                - strategy_name: Selected optimization strategy
                - execution_mode: "sequential" or "parallel"
                - symbol_groups: List of symbol groups for parallel execution
                - parallel_tasks: Number of parallel tasks recommended
                - estimated_speedup: Predicted performance improvement factor
                - estimated_efficiency: Parallel execution efficiency percentage
                - complexity_score: Calculated complexity score
                - complexity_category: "low", "medium", "high", or "extreme"
                - optimization_time_ms: Time taken for optimization analysis
                - memory_estimate_mb: Estimated memory usage
                - reasoning: Human-readable explanation of strategy choice
                - expected_bottleneck: Predicted performance bottleneck
                - scaling_potential: Assessment of parallel scaling potential
        
        Example:
            optimization_result = await performance_optimizer.optimize_simulation_execution(config)
            if optimization_result['execution_mode'] == 'parallel':
                symbol_groups = optimization_result['symbol_groups']
                await performance_optimizer.execute_simulation_groups(symbol_groups, config)
        """
        start_time = self.start_timer("simulation_optimization")
        
        # Use strategy engine
        complexity_analysis = self.strategy_engine.analyze_simulation_complexity(config)
        strategy_decision = self.strategy_engine.determine_optimal_strategy(complexity_analysis)
        
        # Create symbol groups
        symbol_groups = self.strategy_engine.create_symbol_groups(config.symbols, strategy_decision)
        
        # Predict performance gain
        performance_prediction = self.strategy_engine.predict_performance_gain(complexity_analysis, strategy_decision)
        
        # Update metrics
        self.metrics.strategy_decisions[strategy_decision["strategy_name"]] = self.metrics.strategy_decisions.get(strategy_decision["strategy_name"], 0) + 1
        self.metrics.execution_mode_counts[strategy_decision["execution_mode"]] += 1
        self.metrics.symbol_groups_created = len(symbol_groups)
        self.metrics.optimal_group_size = strategy_decision.get("optimal_group_size", 0)
        
        duration = self.end_timer("simulation_optimization", start_time)
        self.metrics.optimization_time_ms = duration
        
        return {
            "strategy_name": strategy_decision["strategy_name"],
            "execution_mode": strategy_decision["execution_mode"],
            "symbol_groups": symbol_groups,
            "parallel_tasks": strategy_decision.get("parallel_tasks", 0),
            "estimated_speedup": performance_prediction["estimated_speedup"],
            "estimated_efficiency": performance_prediction["estimated_efficiency"],
            "complexity_score": complexity_analysis["total_complexity"],
            "complexity_category": complexity_analysis["complexity_category"],
            "optimization_time_ms": duration,
            "symbols_count": len(config.symbols),
            "date_range_days": complexity_analysis["date_range_days"],
            "memory_estimate_mb": performance_prediction["memory_estimate_mb"],
            "recommended_workers": strategy_decision.get("recommended_workers", 1),
            "reasoning": strategy_decision.get("reasoning", ""),
            "expected_bottleneck": strategy_decision.get("expected_bottleneck", "unknown"),
            "scaling_potential": performance_prediction.get("scaling_potential", "unknown")
        }
    
    
    
    async def execute_simulation_groups(self, symbol_groups: List[List[str]], 
                                      config: SimulationConfig, 
                                      group_ids: Optional[List[str]] = None,
                                      execution_service=None) -> List[Dict[str, Any]]:
        """
        Execute simulation groups with real parallel processing using ExecutionService.
        
        Performs intelligent execution strategy selection and runs simulation groups
        either sequentially or in parallel based on group count and system capabilities.
        Integrates with C++ trading engine through ExecutionService for actual execution.
        
        Args:
            symbol_groups (List[List[str]]): List of symbol groups to execute. Each group
                                           contains a list of stock symbols to simulate together.
            config (SimulationConfig): Base simulation configuration that will be applied
                                     to each group with group-specific symbol overrides.
            group_ids (Optional[List[str]]): Pre-generated group IDs for progress tracking.
                                           If None, IDs will be generated automatically.
            execution_service: Shared ExecutionService instance for consistent progress tracking.
        
        Returns:
            List[Dict[str, Any]]: List of execution results, one per group containing:
                - group_id: Unique identifier for the group
                - symbols: List of symbols in this group
                - status: "completed", "failed", or "cancelled"
                - execution_time_ms: Actual execution time for this group
                - simulation_id: Unique simulation ID generated for this group
                - result_data: Parsed JSON results from C++ engine (if successful)
                - return_code: C++ engine return code
                - error: Error message (if failed)
                - raw_output/stderr: Debugging information (if failed)
        
        Notes:
            - Automatically chooses sequential execution for single groups
            - Uses asyncio.gather() for true parallel execution of multiple groups
            - Each group gets its own ExecutionService instance and unique simulation ID
            - Comprehensive error handling with detailed diagnostic information
            - Real-time performance metrics tracking including speedup and efficiency
            - Updates optimizer metrics for parallel vs sequential execution counts
        
        Example:
            symbol_groups = [['AAPL', 'GOOGL'], ['MSFT', 'AMZN'], ['TSLA', 'NVDA']]
            results = await performance_optimizer.execute_simulation_groups(symbol_groups, config)
            for result in results:
                if result['status'] == 'completed':
                    print(f"Group {result['group_id']} completed in {result['execution_time_ms']}ms")
        """
        start_time = self.start_timer("parallel_execution")
        
        # Determine execution strategy based on group count
        if len(symbol_groups) <= 1:
            # Single group - execute sequentially
            results = await self._execute_sequential_groups(symbol_groups, config, group_ids, execution_service)
        else:
            # Multiple groups - execute in parallel
            results = await self._execute_parallel_groups(symbol_groups, config, group_ids, execution_service)
        
        # Update metrics
        duration = self.end_timer("parallel_execution", start_time)
        self.metrics.parallel_tasks = len(symbol_groups)
        self.metrics.parallel_speedup_achieved = self._calculate_achieved_speedup(results, duration)
        self.metrics.parallel_efficiency = self.metrics.parallel_speedup_achieved / len(symbol_groups) if len(symbol_groups) > 0 else 0.0
        
        # Update execution mode counts
        mode = "sequential" if len(symbol_groups) <= 1 else "parallel"
        self.metrics.execution_mode_counts[mode] += 1
        
        logger.info(f"Parallel execution completed in {duration:.2f}ms with {len(symbol_groups)} groups")
        return results
    
    async def _execute_sequential_groups(self, symbol_groups: List[List[str]], config: SimulationConfig, group_ids: Optional[List[str]] = None, execution_service=None) -> List[Dict[str, Any]]:
        # Execute groups sequentially for single/small simulations
        results = []
        
        for i, symbol_group in enumerate(symbol_groups):
            group_start_time = self.start_timer(f"sequential_group_{i}")
            
            # Use pre-generated group ID if available, otherwise generate one
            actual_group_id = group_ids[i] if group_ids and i < len(group_ids) else f"group_{i}_{str(uuid.uuid4())[:8]}"
            
            try:
                # Execute single group with specific group ID
                group_result = await self._execute_single_group(actual_group_id, symbol_group, config, execution_service)
                results.append(group_result)
                
                # Update sequential task count
                self.metrics.sequential_tasks += 1
                
            except Exception as e:
                logger.error(f"Sequential group {actual_group_id} execution failed: {e}")
                results.append({
                    "group_id": actual_group_id,
                    "symbols": symbol_group,
                    "status": "failed",
                    "error": str(e),
                    "execution_time_ms": 0.0,
                    "simulation_id": actual_group_id
                })
            finally:
                self.end_timer(f"sequential_group_{i}", group_start_time)
        
        return results
    
    async def _execute_parallel_groups(self, symbol_groups: List[List[str]], config: SimulationConfig, group_ids: Optional[List[str]] = None, execution_service=None) -> List[Dict[str, Any]]:
        # Execute multiple groups in parallel using asyncio.gather
        parallel_start_time = self.start_timer("parallel_group_execution")
        
        try:
            # Create coroutines for each group
            group_tasks = []
            for i, symbol_group in enumerate(symbol_groups):
                # Use pre-generated group ID if available, otherwise generate one
                actual_group_id = group_ids[i] if group_ids and i < len(group_ids) else f"group_{i}_{str(uuid.uuid4())[:8]}"
                task = self._execute_single_group(actual_group_id, symbol_group, config, execution_service)
                group_tasks.append(task)
            
            # Execute all groups in parallel
            results = await asyncio.gather(*group_tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    actual_group_id = group_ids[i] if group_ids and i < len(group_ids) else f"group_{i}_{str(uuid.uuid4())[:8]}"
                    logger.error(f"Parallel group {actual_group_id} execution failed: {result}")
                    processed_results.append({
                        "group_id": actual_group_id,
                        "symbols": symbol_groups[i],
                        "status": "failed",
                        "error": str(result),
                        "execution_time_ms": 0.0,
                        "simulation_id": actual_group_id
                    })
                else:
                    processed_results.append(result)
                    
            # Update parallel task count
            self.metrics.parallel_tasks += len(symbol_groups)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            # Return error results for all groups
            return [{
                "group_id": group_ids[i] if group_ids and i < len(group_ids) else f"group_{i}_{str(uuid.uuid4())[:8]}",
                "symbols": symbol_group,
                "status": "failed",
                "error": f"Parallel execution error: {str(e)}",
                "execution_time_ms": 0.0,
                "simulation_id": group_ids[i] if group_ids and i < len(group_ids) else f"group_{i}_{str(uuid.uuid4())[:8]}"
            } for i, symbol_group in enumerate(symbol_groups)]
        finally:
            self.end_timer("parallel_group_execution", parallel_start_time)
    
    async def _execute_single_group(self, group_id: str, symbol_group: List[str], config: SimulationConfig, execution_service=None) -> Dict[str, Any]:
        # Execute simulation for a single group of symbols
        group_start_time = self.start_timer(f"group_{group_id}_execution")
        
        try:
            # Use provided execution service or create a new one as fallback
            if execution_service is None:
                # Fallback: create a new execution service instance
                from services.execution_service import ExecutionService
                from pathlib import Path
                cpp_engine_path = Path("/shared/trading_engine")
                execution_service = ExecutionService(cpp_engine_path)
            
            # Create modified config for this group
            group_config = SimulationConfig(
                symbols=symbol_group,
                start_date=config.start_date,
                end_date=config.end_date,
                starting_capital=config.starting_capital,
                strategy=config.strategy,
                strategy_parameters=config.strategy_parameters
            )
            
            # Use the provided group_id as the simulation ID (it's already unique)
            group_simulation_id = group_id
            
            # Execute the simulation for this group
            execution_result = await execution_service.execute_simulation(
                group_simulation_id, group_config
            )
            
            execution_time = self.end_timer(f"group_{group_id}_execution", group_start_time)
            
            # Process execution result
            if execution_result["return_code"] == 0:
                # Parse result data
                try:
                    import json
                    result_data = json.loads(execution_result["stdout"])
                    
                    return {
                        "group_id": group_id,
                        "symbols": symbol_group,
                        "status": "completed",
                        "execution_time_ms": execution_time,
                        "simulation_id": group_simulation_id,
                        "result_data": result_data,
                        "return_code": execution_result["return_code"]
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse group {group_id} results: {e}")
                    return {
                        "group_id": group_id,
                        "symbols": symbol_group,
                        "status": "failed",
                        "error": f"JSON parse error: {str(e)}",
                        "execution_time_ms": execution_time,
                        "raw_output": execution_result["stdout"][:500]  # First 500 chars for debugging
                    }
            else:
                # Execution failed
                return {
                    "group_id": group_id,
                    "symbols": symbol_group,
                    "status": "failed",
                    "error": f"C++ engine error (code {execution_result['return_code']})",
                    "execution_time_ms": execution_time,
                    "stderr": execution_result["stderr"][:500]  # First 500 chars for debugging
                }
                
        except Exception as e:
            execution_time = self.end_timer(f"group_{group_id}_execution", group_start_time)
            logger.error(f"Group {group_id} execution exception: {e}")
            return {
                "group_id": group_id,
                "symbols": symbol_group,
                "status": "failed",
                "error": f"Execution exception: {str(e)}",
                "execution_time_ms": execution_time
            }
    
    def _calculate_achieved_speedup(self, results: List[Dict[str, Any]], total_duration: float) -> float:
        # Calculate the actual speedup achieved from parallel execution
        if not results:
            return 1.0
        
        # Sum up individual execution times
        individual_times = []
        for result in results:
            exec_time = result.get("execution_time_ms", 0.0)
            if exec_time > 0:
                individual_times.append(exec_time)
        
        if not individual_times:
            return 1.0
        
        # Calculate theoretical sequential time
        sequential_time = sum(individual_times)
        
        # Calculate speedup (sequential time / parallel time)
        if total_duration > 0:
            speedup = sequential_time / total_duration
            return round(speedup, 2)
        
        return 1.0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        # Get cache performance statistics
        total_requests = self.metrics.cache_hits + self.metrics.cache_misses
        hit_rate = (self.metrics.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_enabled": self.cache_enabled,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Enhanced performance summary with comprehensive analytics.
        
        Provides a complete dashboard of Performance Optimizer metrics including:
        - Cache performance statistics
        - Operation timing analytics
        - Parallel execution performance metrics
        - Strategy decision analytics
        - Symbol grouping efficiency metrics
        - Performance regression tracking
        - System configuration status
        
        Returns:
            Dict[str, Any]: Comprehensive performance analytics containing:
                cache_stats: Cache hit rates and performance metrics
                operation_times: Average, min, max times for all operations
                parallel_execution_stats: Parallel task counts, speedup, efficiency
                strategy_analytics: Strategy decisions and execution mode statistics
                grouping_metrics: Symbol grouping efficiency and balance scores
                performance_tracking: Baseline performance and regression detection
                optimization_enabled: System configuration and feature flags
        
        Example:
            summary = performance_optimizer.get_performance_summary()
            print(f"Parallel efficiency: {summary['parallel_execution_stats']['parallel_efficiency']}%")
            print(f"Cache hit rate: {summary['cache_stats']['hit_rate_percent']}%")
        """
        avg_times = {}
        for operation, times in self.operation_times.items():
            avg_times[operation] = {
                "avg_ms": round(sum(times) / len(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "count": len(times)
            }
        
        # Calculate execution mode statistics
        total_executions = sum(self.metrics.execution_mode_counts.values())
        execution_mode_percentages = {}
        if total_executions > 0:
            for mode, count in self.metrics.execution_mode_counts.items():
                execution_mode_percentages[mode] = round((count / total_executions) * 100, 2)
        
        return {
            "cache_stats": self.get_cache_statistics(),
            "operation_times": avg_times,
            
            # Parallel execution metrics
            "parallel_execution_stats": {
                "parallel_tasks_executed": self.metrics.parallel_tasks,
                "sequential_tasks_executed": self.metrics.sequential_tasks,
                "parallel_speedup_achieved": self.metrics.parallel_speedup_achieved,
                "parallel_efficiency": round(self.metrics.parallel_efficiency * 100, 2),  # Convert to percentage
                "worker_utilization": round(self.metrics.worker_utilization * 100, 2)  # Convert to percentage
            },
            
            # Strategy decision analytics
            "strategy_analytics": {
                "strategy_decisions": self.metrics.strategy_decisions,
                "execution_mode_counts": self.metrics.execution_mode_counts,
                "execution_mode_percentages": execution_mode_percentages
            },
            
            # Symbol grouping metrics
            "grouping_metrics": {
                "symbol_groups_created": self.metrics.symbol_groups_created,
                "optimal_group_size": self.metrics.optimal_group_size,
                "group_balance_score": round(self.metrics.group_balance_score * 100, 2)  # Convert to percentage
            },
            
            # Performance regression tracking
            "performance_tracking": {
                "baseline_performance": self.metrics.baseline_performance,
                "regression_detected": self.metrics.performance_regression_detected,
                "optimization_time_ms": self.metrics.optimization_time_ms
            },
            
            # System configuration
            "optimization_enabled": {
                "caching": self.cache_enabled,
                "parallel_processing": self.parallel_enabled,
                "max_workers": self.max_workers,
                "strategy_engine_active": hasattr(self, 'strategy_engine') and self.strategy_engine is not None
            }
        }
    
    async def cleanup(self):
        # Clean up resources
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        logger.info("Performance optimizer cleaned up")

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()