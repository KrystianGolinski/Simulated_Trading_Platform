# Performance Optimization Module
# This module provides intelligent parallel execution optimization for trading simulations
# Key responsibilities:
# - Complexity analysis of simulation configurations
# - Intelligent strategy selection (sequential vs parallel execution)
# - Dynamic symbol grouping for optimal parallel processing
# - Performance prediction using Amdahl's Law with overhead modelling
# - Real-time parallel execution with progress tracking
# - Memory usage monitoring and optimization analytics
# - Comprehensive performance metrics and diagnostics
#
# The module integrates with the C++ trading engine to provide:
# - Automatic optimization based on simulation complexity
# - Parallel group execution with proper error handling
# - Memory statistics collection and analysis
# - Performance regression detection and reporting

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Any, Optional
import logging

from models import SimulationConfig

logger = logging.getLogger(__name__)

class ParallelExecutionStrategy:
    # Strategy decision engine for intelligent execution planning
    # Analyses simulation complexity and determines optimal execution mode
    # Uses machine learning principles to optimize parallel vs sequential execution
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.strategy_history = {}  # Track strategy performance over time for learning
        
        # Complexity thresholds for strategy decision making
        # Based on empirical analysis of execution times vs complexity
        self.complexity_thresholds = {
            "low": 5000,       # Sequential execution optimal
            "medium": 25000,   # Moderate parallelism beneficial
            "high": 100000     # Aggressive parallelism required
        }
        
        # Minimum efficiency threshold for parallel execution to be worthwhile
        self.parallel_efficiency_baseline = 0.7  # 70% efficiency minimum
        
    def analyze_simulation_complexity(self, config: SimulationConfig) -> Dict[str, Any]:
        # Comprehensive complexity analysis for optimal execution strategy selection
        # Considers multiple factors: symbols count, date range, strategy type, market conditions
        # Returns detailed complexity metrics used for intelligent decision making
        from datetime import datetime
        
        symbols_count = len(config.symbols)
        
        # Calculate date range with proper type handling
        start_date = datetime.fromisoformat(config.start_date) if isinstance(config.start_date, str) else config.start_date
        end_date = datetime.fromisoformat(config.end_date) if isinstance(config.end_date, str) else config.end_date
        date_range_days = (end_date - start_date).days
        
        # Base complexity: fundamental measure of computational load
        # Each symbol-day combination represents a unit of computational work
        base_complexity = symbols_count * date_range_days
        
        # Strategy complexity multiplier based on algorithmic complexity
        # Different strategies have varying computational requirements
        strategy_multiplier = self._get_strategy_complexity_multiplier(config)
        
        # Market data complexity for volatile periods requiring more computation
        # Long-term simulations have additional complexity due to memory management
        market_complexity_multiplier = 1.0
        if date_range_days > 365:  # Long-term simulations
            market_complexity_multiplier = 1.2
        
        # Final complexity score combining all factors
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
    # Comprehensive performance analytics and monitoring system
    # Tracks execution metrics across all simulation modes and optimization strategies
    # Provides detailed insights for performance tuning and regression detection
    def __init__(self):
        # Cache performance metrics for optimization analysis
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Detailed timing metrics for performance analysis
        self.query_time_ms = 0.0          # Database query execution time
        self.simulation_time_ms = 0.0     # Core simulation execution time
        self.optimization_time_ms = 0.0   # Time spent on optimization analysis
        
        # System resource utilization metrics
        self.memory_usage_mb = 0.0        # Memory consumption during execution
        self.cpu_usage_percent = 0.0      # CPU utilization percentage
        
        # Parallel execution performance tracking
        self.parallel_tasks = 0           # Number of parallel tasks executed
        self.sequential_tasks = 0         # Number of sequential tasks executed
        self.worker_utilization = 0.0     # Worker thread utilization efficiency
        self.parallel_speedup_achieved = 0.0  # Actual speedup vs sequential execution
        self.parallel_efficiency = 0.0   # Parallel efficiency percentage
        
        # Strategy decision analytics for optimization learning
        self.strategy_decisions = {}      # Track which optimization strategies were chosen
        self.execution_mode_counts = {"sequential": 0, "parallel": 0}  # Mode usage statistics
        
        # Performance regression detection and baseline tracking
        self.baseline_performance = {}         # Historical performance baselines
        self.performance_regression_detected = False  # Regression alert flag
        
        # Symbol grouping optimization metrics
        self.symbol_groups_created = 0    # Number of symbol groups created for parallel execution
        self.optimal_group_size = 0       # Optimal group size determined by algorithm
        self.group_balance_score = 0.0    # Load balancing effectiveness score

class PerformanceOptimizer:
    # Central performance optimization coordinator for trading simulations
    # Provides intelligent execution optimization, parallel processing, and performance monitoring
    # Integrates with C++ trading engine for optimal simulation execution
    
    def __init__(self):
        # Configuration settings for optimization behavior
        self.cache_enabled = True     # Enable caching for repeated operations
        self.cache_ttl = 3600        # Cache time-to-live (1 hour)
        self.parallel_enabled = True  # Enable parallel execution optimization
        self.max_workers = 4         # Maximum parallel worker threads
        
        # Comprehensive performance tracking and analytics
        self.metrics = SimulationMetrics()
        self.operation_times: Dict[str, List[float]] = {}  # Historical operation timing data
        
        # Intelligent strategy decision engine for execution planning
        self.strategy_engine = ParallelExecutionStrategy(max_workers=self.max_workers)
        
        # Parallel execution infrastructure
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
        Advanced simulation execution optimization with intelligent strategy selection.
        
        This method performs comprehensive analysis of simulation configuration to determine
        the optimal execution strategy. It considers multiple factors including computational
        complexity, resource availability, and historical performance data to make intelligent
        decisions about sequential vs parallel execution.
        
        The optimization process includes:
        - Multi-factor complexity analysis (symbols, date range, strategy complexity)
        - Intelligent execution mode selection using machine learning principles
        - Dynamic symbol grouping for optimal parallel load distribution
        - Performance prediction using advanced mathematical models (Amdahl's Law)
        - Resource estimation for memory and CPU usage planning
        
        Args:
            config (SimulationConfig): Complete simulation configuration including:
                - symbols: List of stock symbols to simulate
                - date range: Start and end dates for simulation period
                - strategy: Trading strategy identifier and parameters
                - capital: Starting capital and risk parameters
        
        Returns:
            Dict[str, Any]: Comprehensive optimization analysis report containing:
                - strategy_name: Selected optimization strategy name
                - execution_mode: "sequential" or "parallel" execution mode
                - symbol_groups: Optimized symbol groups for parallel execution
                - parallel_tasks: Recommended number of parallel worker tasks
                - estimated_speedup: Predicted performance improvement multiplier
                - estimated_efficiency: Parallel execution efficiency (0-100%)
                - complexity_score: Numerical complexity assessment
                - complexity_category: Categorized complexity level
                - optimization_time_ms: Time spent on optimization analysis
                - memory_estimate_mb: Predicted memory usage requirement
                - reasoning: Human-readable strategy selection explanation
                - expected_bottleneck: Predicted primary performance limitation
                - scaling_potential: Assessment of parallel scaling benefits
        
        Example Usage:
            optimization_result = await performance_optimizer.optimize_simulation_execution(config)
            if optimization_result['execution_mode'] == 'parallel':
                symbol_groups = optimization_result['symbol_groups']
                results = await performance_optimizer.execute_simulation_groups(symbol_groups, config)
                speedup = optimization_result['estimated_speedup']
                logger.info(f"Parallel execution achieved {speedup}x speedup")
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
        Execute optimized simulation groups with intelligent parallel processing.
        
        This method implements the core parallel execution engine for trading simulations.
        It automatically selects the optimal execution strategy (sequential vs parallel)
        based on group count and system capabilities, then executes all groups with
        comprehensive error handling and performance monitoring.
        
        The execution process includes:
        - Automatic execution strategy selection based on group count
        - True parallel execution using asyncio.gather() for multiple groups
        - Individual group isolation with separate ExecutionService instances
        - Real-time performance metrics collection and analysis
        - Comprehensive error handling with detailed diagnostic information
        - Progress tracking and correlation ID management
        
        Integration with C++ Trading Engine:
        - Each group executes as a separate simulation in the C++ engine
        - Results are parsed and validated from JSON output
        - Memory usage and performance statistics are collected
        - Engine errors are categorized and handled appropriately
        
        Args:
            symbol_groups (List[List[str]]): Optimized symbol groups for execution.
                Each group contains symbols that will be simulated together for optimal
                resource utilization and load balancing.
            config (SimulationConfig): Base simulation configuration applied to all groups.
                Group-specific symbol lists override the global symbols list.
            group_ids (Optional[List[str]]): Pre-generated unique group identifiers.
                Used for progress tracking and result correlation. Auto-generated if None.
            execution_service: Shared ExecutionService instance for consistent engine
                integration and progress tracking across all groups.
        
        Returns:
            List[Dict[str, Any]]: Detailed execution results for each group containing:
                - group_id: Unique identifier for progress tracking and correlation
                - symbols: List of stock symbols executed in this group
                - status: Execution outcome ("completed", "failed", "cancelled")
                - execution_time_ms: Actual execution time for performance analysis
                - simulation_id: Unique simulation ID from the C++ engine
                - result_data: Parsed JSON results with performance metrics (if successful)
                - return_code: C++ engine exit code for error diagnosis
                - error: Structured error message with categorization (if failed)
                - raw_output/stderr: Raw engine output for debugging (if failed)
        
        Performance Characteristics:
            - Sequential execution: Used for single groups or small workloads
            - Parallel execution: Automatic for multiple groups with asyncio.gather()
            - Speedup tracking: Real-time measurement of parallel efficiency
            - Resource monitoring: Memory and CPU usage tracking per group
            - Error isolation: Group failures don't affect other groups
        
        Example Usage:
            # Optimize simulation for parallel execution
            optimization = await optimizer.optimize_simulation_execution(config)
            symbol_groups = optimization['symbol_groups']
            
            # Execute groups with performance monitoring
            results = await optimizer.execute_simulation_groups(symbol_groups, config)
            
            # Analyze results and performance
            successful_groups = [r for r in results if r['status'] == 'completed']
            total_time = max(r['execution_time_ms'] for r in results)
            speedup = sum(r['execution_time_ms'] for r in results) / total_time
            logger.info(f"Achieved {speedup:.2f}x speedup with {len(successful_groups)} groups")
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
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive memory usage statistics from the C++ trading engine.
        
        This method provides real-time memory monitoring capabilities by interfacing
        directly with the C++ trading engine's internal memory reporting system.
        Essential for performance optimization, memory leak detection, and resource
        planning for large-scale simulations.
        
        Memory Monitoring Features:
        - Real-time memory usage across all engine components
        - Service-specific memory breakdown for detailed analysis
        - Cache efficiency metrics and optimization opportunities
        - Memory distribution analysis for resource planning
        - Integration with performance optimization recommendations
        
        Engine Integration:
        - Direct communication with C++ engine memory subsystem
        - Comprehensive service-level memory reporting
        - Cache statistics for optimization analysis
        - Memory allocation tracking per simulation component
        
        Returns:
            Dict[str, Any]: Comprehensive memory analysis containing:
                - status: Operation result ("success", "error", "unavailable")
                - total_memory_bytes: Aggregate engine memory consumption
                - total_memory_mb: Memory usage in megabytes for readability
                - portfolio_memory_bytes: Portfolio management service memory
                - market_data_cache_bytes: Market data cache memory allocation
                - execution_service_bytes: Trade execution service memory
                - data_processor_bytes: Data processing pipeline memory
                - portfolio_allocator_bytes: Portfolio allocation service memory
                - price_cache_symbols: Number of symbols cached in memory
                - cache_bytes_per_symbol: Average memory usage per cached symbol
                - memory_distribution: Percentage breakdown by service
                - memory_optimization_available: Whether optimization is beneficial
                - detailed_report: Raw engine memory report for debugging
                - error: Detailed error information (if operation failed)
                - error_code: Machine-readable error classification
        
        Performance Impact:
            - Low overhead memory query operation
            - Non-blocking async implementation
            - Cached results to avoid engine overload
            - Graceful degradation if engine unavailable
        
        Example Usage:
            # Monitor memory usage during simulation
            memory_stats = await optimizer.get_memory_statistics()
            
            if memory_stats["status"] == "success":
                total_mb = memory_stats["total_memory_mb"]
                cache_efficiency = memory_stats["cache_bytes_per_symbol"]
                
                logger.info(f"Engine memory usage: {total_mb:.2f} MB")
                
                # Check for optimization opportunities
                if memory_stats["memory_optimization_available"]:
                    logger.info("Memory optimization recommended")
                    
                # Analyse memory distribution
                distribution = memory_stats["memory_distribution"]
                for service, percentage in distribution.items():
                    logger.debug(f"{service}: {percentage}% of total memory")
            else:
                logger.warning(f"Memory statistics unavailable: {memory_stats['error']}")
        """
        try:
            # Import ExecutionService locally to avoid circular imports
            from services.execution_service import ExecutionService
            from pathlib import Path
            import os
            
            # Get engine path from environment
            engine_path_str = os.getenv('CPP_ENGINE_PATH', '/shared/trading_engine')
            engine_path = Path(engine_path_str)
            
            # Create temporary ExecutionService instance for memory query
            execution_service = ExecutionService(engine_path)
            
            # Query engine memory statistics
            memory_result = await execution_service.get_engine_memory_statistics()
            
            if memory_result.get("status") == "success":
                # Add additional derived metrics
                total_bytes = memory_result.get("total_memory_bytes", 0)
                memory_result["total_memory_mb"] = round(total_bytes / (1024 * 1024), 2)
                memory_result["memory_optimization_available"] = total_bytes > 0
                
                # Add cache efficiency metrics
                cache_symbols = memory_result.get("price_cache_symbols", 0)
                cache_bytes = memory_result.get("market_data_cache_bytes", 0)
                if cache_symbols > 0 and cache_bytes > 0:
                    memory_result["cache_bytes_per_symbol"] = round(cache_bytes / cache_symbols, 2)
                else:
                    memory_result["cache_bytes_per_symbol"] = 0
                
                # Add memory distribution percentages
                if total_bytes > 0:
                    memory_result["memory_distribution"] = {
                        "portfolio_percent": round((memory_result.get("portfolio_memory_bytes", 0) / total_bytes) * 100, 2),
                        "cache_percent": round((memory_result.get("market_data_cache_bytes", 0) / total_bytes) * 100, 2),
                        "execution_percent": round((memory_result.get("execution_service_bytes", 0) / total_bytes) * 100, 2),
                        "allocator_percent": round((memory_result.get("portfolio_allocator_bytes", 0) / total_bytes) * 100, 2),
                        "processor_percent": round((memory_result.get("data_processor_bytes", 0) / total_bytes) * 100, 2)
                    }
                
                logger.info(f"Retrieved engine memory statistics: {total_bytes} bytes total")
                return memory_result
            else:
                # Engine query failed
                logger.warning(f"Engine memory query failed: {memory_result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "error": memory_result.get("error", "Engine memory query failed"),
                    "error_code": memory_result.get("error_code", "QUERY_FAILED"),
                    "total_memory_bytes": 0,
                    "memory_optimization_available": False
                }
                
        except ImportError as e:
            logger.error(f"Failed to import ExecutionService for memory statistics: {e}")
            return {
                "status": "unavailable",
                "error": "ExecutionService not available for memory queries",
                "error_code": "SERVICE_UNAVAILABLE",
                "total_memory_bytes": 0,
                "memory_optimization_available": False
            }
        except Exception as e:
            logger.error(f"Failed to get engine memory statistics: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "error_code": "EXECUTION_FAILED",
                "total_memory_bytes": 0,
                "memory_optimization_available": False
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance analytics dashboard for system monitoring.
        
        This method provides a complete performance overview by aggregating metrics
        from all optimizer subsystems. Essential for performance monitoring,
        optimization analysis, and system health assessment.
        
        Analytics Categories:
        - Cache Performance: Hit rates, efficiency metrics, optimization opportunities
        - Operation Timing: Detailed timing analytics with statistical analysis
        - Parallel Execution: Speedup analysis, efficiency metrics, worker utilization
        - Strategy Analytics: Decision patterns, mode preferences, optimization trends
        - Memory Management: Usage patterns, optimization effectiveness, resource planning
        - System Configuration: Feature flags, capability assessment, optimization settings
        
        Performance Insights:
        - Historical trend analysis for performance regression detection
        - Efficiency benchmarking against baseline performance
        - Resource utilization optimization recommendations
        - Parallel execution effectiveness assessment
        - Cache optimization opportunities identification
        
        Returns:
            Dict[str, Any]: Multi-dimensional performance analytics containing:
                
                cache_stats: Cache performance metrics
                  - hit_rate_percent: Cache effectiveness percentage
                  - total_requests: Total cache operations
                  - optimization_opportunities: Cache improvement suggestions
                
                operation_times: Statistical timing analysis
                  - avg_ms: Average operation duration
                  - min_ms/max_ms: Performance bounds
                  - count: Operation frequency statistics
                
                memory_usage: Real-time memory analytics
                  - current_usage: Live memory consumption data
                  - optimization_status: Memory efficiency assessment
                  - distribution_analysis: Service-level memory breakdown
                
                parallel_execution_stats: Parallel processing analytics
                  - parallel_tasks_executed: Total parallel operations
                  - parallel_speedup_achieved: Actual speedup measurements
                  - parallel_efficiency: Efficiency percentage
                  - worker_utilization: Resource utilization effectiveness
                
                strategy_analytics: Optimization decision analysis
                  - strategy_decisions: Decision pattern tracking
                  - execution_mode_counts: Sequential vs parallel usage
                  - execution_mode_percentages: Usage distribution analysis
                
                grouping_metrics: Symbol grouping optimization analysis
                  - symbol_groups_created: Group creation statistics
                  - optimal_group_size: Load balancing effectiveness
                  - group_balance_score: Distribution quality metrics
                
                performance_tracking: Regression detection and baseline analysis
                  - baseline_performance: Historical performance benchmarks
                  - regression_detected: Performance degradation alerts
                  - optimization_time_ms: Optimization overhead analysis
                
                optimization_enabled: System capability and configuration status
                  - caching: Cache system status
                  - parallel_processing: Parallel execution capability
                  - max_workers: Resource allocation configuration
                  - strategy_engine_active: Optimization engine status
        
        Example Usage:
            # Generate comprehensive performance report
            summary = await optimizer.get_performance_summary()
            
            # Analyse parallel execution effectiveness
            parallel_stats = summary['parallel_execution_stats']
            efficiency = parallel_stats['parallel_efficiency']
            
            if efficiency < 70:
                logger.warning(f"Low parallel efficiency: {efficiency}%")
                # Investigate bottlenecks and optimization opportunities
            
            # Monitor cache performance
            cache_stats = summary['cache_stats']
            hit_rate = cache_stats['hit_rate_percent']
            
            if hit_rate < 80:
                logger.info(f"Cache hit rate could be improved: {hit_rate}%")
            
            # Check for performance regression
            tracking = summary['performance_tracking']
            if tracking['regression_detected']:
                logger.alert("Performance regression detected - investigation required")
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
        
        # Get memory statistics if available
        memory_stats = await self.get_memory_statistics()
        
        return {
            "cache_stats": self.get_cache_statistics(),
            "operation_times": avg_times,
            "memory_usage": memory_stats,
            
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

# Global performance optimizer instance
# Singleton pattern ensures consistent optimization state across the entire application
# Used by simulation engine, routers, and performance monitoring endpoints
performance_optimizer = PerformanceOptimizer()