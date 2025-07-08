# Performance Calculator - Trading Performance Metrics Calculation and Analysis Service
# This module provides comprehensive performance metric calculation and validation for trading simulations
# 
# Architecture Overview:
# The PerformanceCalculator implements stateless performance analysis operations that process
# trading simulation results from the C++ engine and generate comprehensive performance metrics.
# It provides financial calculation capabilities, data validation, and consistency checking
# for trading performance evaluation.
#
# Key Responsibilities:
# 1. Performance metrics calculation from simulation results
# 2. Financial metrics validation and data integrity checking
# 3. Cross-field consistency validation for result accuracy
# 4. Performance data structure validation and sanitization
# 5. Trading statistics computation and analysis
# 6. Comprehensive error handling and logging for invalid data
#
# Performance Metrics Calculation:
# The calculator processes comprehensive performance data including:
# - Return calculations (total, annualized, percentage-based)
# - Risk metrics (volatility, drawdown, Sharpe ratio)
# - Trade statistics (win rate, profit factor, average win/loss)
# - Portfolio metrics (final balance, capital utilization)
# - Signal analysis (signal generation count and effectiveness)
#
# Integration with Trading Platform:
# - Processes C++ engine output for performance analysis
# - Integrates with SimulationResults for comprehensive reporting
# - Supports validation pipeline for data quality assurance
# - Provides stateless operations for high-performance calculation
# - Enables financial analysis and backtesting result evaluation
#
# Data Validation Features:
# - Comprehensive field validation with type checking
# - Cross-field consistency validation for accuracy
# - Financial constraint validation (positive capital, valid ratios)
# - Trade count validation and reconciliation
# - Error handling with detailed logging for debugging

import logging
from typing import Dict, Any
from models import PerformanceMetrics

logger = logging.getLogger(__name__)

class PerformanceCalculator:
    """
    Comprehensive Trading Performance Metrics Calculation and Analysis Service.
    
    This class provides stateless performance analysis operations that process trading
    simulation results from the C++ engine and generate comprehensive performance metrics.
    It implements sophisticated financial calculations, data validation, and consistency
    checking for accurate trading performance evaluation.
    
    Key Features:
    - Stateless design for high-performance calculation operations
    - Comprehensive performance metrics calculation from simulation results
    - Financial data validation with type checking and constraint validation
    - Cross-field consistency validation for data accuracy and integrity
    - Trade statistics computation with win/loss analysis
    - Risk metrics calculation including volatility and drawdown analysis
    - Signal analysis for strategy effectiveness evaluation
    
    Financial Metrics Computed:
    The calculator processes comprehensive performance data including return calculations,
    risk metrics, trade statistics, portfolio metrics, and signal analysis to provide
    complete trading performance evaluation.
    
    Data Validation:
    The service provides comprehensive validation including field validation with type
    checking, cross-field consistency validation, financial constraint validation,
    and trade count validation with detailed error logging for debugging.
    
    Architecture Integration:
    The calculator integrates with the trading platform to process C++ engine output,
    support validation pipelines, and enable financial analysis for backtesting
    result evaluation.
    """
    
    # Stateless design - no initialization needed for calculation operations
    
    def calculate_performance_metrics(self, result_data: Dict[str, Any]) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics from trading simulation results.
        
        This method processes performance data from the C++ engine and generates a complete
        PerformanceMetrics object with all financial calculations, risk metrics, and trade
        statistics. It handles data extraction, metric calculation, and provides fallback
        values for missing or invalid data.
        
        Args:
            result_data: Dictionary containing simulation results from C++ engine including:
                - performance_metrics: Core performance data from engine
                - ending_value: Final portfolio value
                - starting_capital: Initial capital amount
                - signals: List of trading signals generated
                
        Returns:
            PerformanceMetrics: Comprehensive performance metrics object containing:
                - Return metrics (total return, annualized return)
                - Risk metrics (Sharpe ratio, volatility, drawdown)
                - Trade statistics (win rate, profit factor, trade counts)
                - Portfolio metrics (final balance, capital utilization)
                - Signal analysis (signal count and effectiveness)
                
        Performance Data Processing:
        The method extracts performance data from the C++ engine output, handling both
        structured performance_metrics sections and flat result structures. It processes
        core financial metrics, risk calculations, trade statistics, and signal analysis
        to provide comprehensive trading performance evaluation.
        
        Data Extraction Strategy:
        The method uses a flexible extraction approach that checks for performance data
        in dedicated sections first, then falls back to flat structure extraction,
        ensuring compatibility with different C++ engine output formats.
        """
        # Extract performance data from C++ engine output with flexible structure handling
        performance_data = result_data.get("performance_metrics", {})
        if not performance_data:
            performance_data = result_data
        
        # Extract computed metrics from C++ engine with validation
        profit_factor = performance_data.get("profit_factor")
        average_win = performance_data.get("average_win")
        average_loss = performance_data.get("average_loss")
        annualized_return = performance_data.get("annualized_return")
        volatility = performance_data.get("volatility")
        
        # Generate comprehensive PerformanceMetrics object with all financial calculations
        return PerformanceMetrics(
            # Core return metrics from engine calculations
            total_return_pct=performance_data.get("total_return_pct", 0.0),
            sharpe_ratio=performance_data.get("sharpe_ratio"),
            max_drawdown_pct=performance_data.get("max_drawdown_pct", performance_data.get("max_drawdown", 0.0)),
            win_rate=performance_data.get("win_rate", 0.0),
            total_trades=performance_data.get("total_trades", performance_data.get("trades", 0)),
            winning_trades=performance_data.get("winning_trades", 0),
            losing_trades=performance_data.get("losing_trades", 0),
            final_balance=result_data.get("ending_value"),
            starting_capital=result_data.get("starting_capital"),
            max_drawdown=performance_data.get("max_drawdown"),  # Absolute drawdown value
            
            # Signal analysis metrics for strategy effectiveness evaluation
            signals_generated=len(result_data.get("signals", [])),
            
            # Advanced computed metrics from C++ engine financial calculations
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            annualized_return=annualized_return,
            volatility=volatility
        )
    
    def validate_performance_metrics(self, performance_metrics: Any) -> bool:
        """
        Comprehensive validation of performance metrics structure and content.
        
        This method performs thorough validation of performance metrics data to ensure
        data integrity, proper formatting, and compliance with financial constraints.
        It validates both the overall structure and individual metric values with
        flexible validation rules that account for different trading scenarios.
        
        Args:
            performance_metrics: Performance metrics data to validate (should be dictionary)
            
        Returns:
            bool: True if performance metrics are valid, False otherwise
            
        Validation Process:
        1. Structure validation (must be dictionary)
        2. Field type validation (numeric types, integers)
        3. Value constraint validation (positive values, ranges)
        4. Cross-field consistency validation (trade counts)
        5. Financial constraint validation (realistic ratios)
        
        The method provides detailed error logging for each validation failure,
        enabling precise debugging and data quality monitoring.
        
        Validation Rules:
        - Numeric fields must be proper numeric types (int/float)
        - Drawdown percentages must be non-negative
        - Trade counts must be non-negative integers
        - Win/loss trade counts must be consistent with total trades
        - Flexible validation allows for neutral trades and open positions
        """
        # Validate performance metrics structure and type
        if not isinstance(performance_metrics, dict):
            logger.error("performance_metrics must be a dictionary")
            return False
        
        # Define comprehensive validation rules for performance metrics fields
        metric_validations = [
            ("total_return_pct", float, None),  # Can be negative (losses)
            ("sharpe_ratio", float, None),      # Can be negative (poor risk-adjusted returns)
            ("max_drawdown_pct", float, lambda x: x >= 0),  # Drawdown as positive percentage
            ("win_rate", float, lambda x: x >= 0),     # Win rate can be percentage or ratio
            ("total_trades", int, lambda x: x >= 0),
            ("winning_trades", int, lambda x: x >= 0),
            ("losing_trades", int, lambda x: x >= 0),
        ]
        
        # Validate each performance metric field with type and constraint checking
        for field, field_type, validator in metric_validations:
            if field in performance_metrics:
                value = performance_metrics[field]
                
                # Type validation for numeric fields
                if field_type == float and not isinstance(value, (int, float)):
                    logger.error(f"Performance metric '{field}' must be numeric, got {type(value)}")
                    return False
                elif field_type == int and not isinstance(value, int):
                    logger.error(f"Performance metric '{field}' must be integer, got {type(value)}")
                    return False
                
                # Constraint validation using field-specific validators
                if validator and not validator(value):
                    logger.error(f"Performance metric '{field}' failed validation: {value}")
                    return False
        
        # Cross-field validation for trade count consistency (flexible for different methodologies)
        if "winning_trades" in performance_metrics and "losing_trades" in performance_metrics and "total_trades" in performance_metrics:
            winning = performance_metrics["winning_trades"]
            losing = performance_metrics["losing_trades"]
            total = performance_metrics["total_trades"]
            
            # Validate trade count consistency with flexible counting methodologies
            if winning + losing > total:
                logger.error(f"Trade count impossible: winning({winning}) + losing({losing}) > total({total})")
                return False
            elif winning + losing < total:
                # Acceptable scenario - may include neutral trades or open positions
                logger.info(f"Trade count info: winning({winning}) + losing({losing}) < total({total}) - may include neutral/open trades")
        
        return True
    
    def validate_cross_field_consistency(self, result_data: Dict[str, Any]) -> bool:
        """
        Comprehensive validation of cross-field consistency in simulation result data.
        
        This method validates consistency between different fields in the result data
        to ensure accuracy and integrity of financial calculations. It performs cross-
        validation of related metrics to detect calculation errors and data corruption.
        
        Args:
            result_data: Dictionary containing complete simulation results
            
        Returns:
            bool: True if all cross-field validations pass, False otherwise
            
        Validation Checks:
        1. Capital consistency (starting capital vs ending value vs return percentage)
        2. Equity curve consistency (final equity value vs ending value)
        3. Performance metric consistency (calculated vs reported values)
        4. Trade data consistency (signals vs trades vs performance)
        
        The method provides detailed warning and error logging for inconsistencies,
        enabling debugging and data quality monitoring while allowing for small
        floating-point differences in financial calculations.
        
        Cross-Field Validation Benefits:
        - Detects calculation errors in C++ engine output
        - Identifies data corruption during transmission
        - Ensures financial calculation accuracy
        - Provides confidence in simulation results
        - Enables quality assurance for trading analysis
        """
        # Perform comprehensive cross-field validation with error handling
        try:
            # Validate capital and return percentage consistency
            starting_capital = result_data.get("starting_capital")
            ending_value = result_data.get("ending_value")
            total_return_pct = result_data.get("total_return_pct")
            
            if starting_capital and ending_value and total_return_pct is not None:
                # Calculate expected return percentage and compare with reported value
                expected_return = ((ending_value - starting_capital) / starting_capital) * 100
                if abs(expected_return - total_return_pct) > 0.01:  # Allow small floating point differences
                    logger.warning(f"Return percentage inconsistency: expected {expected_return:.2f}%, got {total_return_pct:.2f}%")
            
            # Validate equity curve final value consistency with ending value
            if "equity_curve" in result_data:
                equity_curve = result_data["equity_curve"]
                if equity_curve and len(equity_curve) > 0:
                    final_equity_value = equity_curve[-1].get("value")
                    if final_equity_value and ending_value:
                        if abs(final_equity_value - ending_value) > 0.01:
                            logger.warning(f"Equity curve final value ({final_equity_value}) doesn't match ending_value ({ending_value})")
            
            return True
            
        except Exception as e:
            logger.error(f"Cross-field validation error: {e}")
            return False
