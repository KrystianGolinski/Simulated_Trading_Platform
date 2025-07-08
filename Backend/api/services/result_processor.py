# Result Processor - Comprehensive Simulation Result Processing and Management Service
# This module provides advanced result processing capabilities for trading simulation results
# 
# Architecture Overview:
# The ResultProcessor implements sophisticated result processing and management for trading
# simulations, coordinating multiple specialized processors to transform raw C++ engine output
# into structured, validated SimulationResults objects. It provides comprehensive result
# lifecycle management, data validation, and storage capabilities.
#
# Key Responsibilities:
# 1. Simulation result lifecycle management (initialization, processing, storage)
# 2. Comprehensive result data processing using specialized processor coordination
# 3. JSON parsing and validation of C++ engine output
# 4. Result data structure validation and integrity checking
# 5. Performance metrics calculation and trade conversion coordination
# 6. Result storage management with cleanup and retrieval capabilities
# 7. Error handling and status management throughout processing pipeline
#
# Processing Pipeline:
# 1. Initialize simulation result with pending status
# 2. Parse and validate JSON output from C++ engine
# 3. Process performance metrics using PerformanceCalculator
# 4. Convert trading signals to trade records using TradeConverter
# 5. Process equity curve data using EquityProcessor
# 6. Update simulation status and completion timestamps
# 7. Store processed results for retrieval and analysis
#
# Integration with Trading Platform:
# - Coordinates specialized processors for comprehensive result processing
# - Provides centralized result storage and retrieval capabilities
# - Integrates with simulation lifecycle management
# - Supports result validation and data quality assurance
# - Enables comprehensive error handling and status tracking
# - Facilitates result cleanup and resource management
#
# Specialized Processor Coordination:
# - PerformanceCalculator: Financial metrics and validation
# - TradeConverter: Signal-to-trade conversion and validation
# - EquityProcessor: Equity curve processing and validation
# - Integrated validation pipeline for comprehensive data quality
#
# Result Storage Features:
# - In-memory result storage with simulation lifecycle tracking
# - Automatic cleanup of old results based on configurable age
# - Comprehensive status management (pending, running, completed, failed)
# - Error handling with detailed error message storage
# - Result retrieval capabilities for individual and batch access

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from models import SimulationResults, SimulationStatus, SimulationConfig
from .performance_calculator import PerformanceCalculator
from .trade_converter import TradeConverter
from .equity_processor import EquityProcessor

logger = logging.getLogger(__name__)

class ResultProcessor:
    """
    Comprehensive Simulation Result Processing and Management Service.
    
    This class provides advanced result processing capabilities for trading simulations,
    coordinating multiple specialized processors to transform raw C++ engine output into
    structured, validated SimulationResults objects. It implements sophisticated result
    lifecycle management, data validation, and storage capabilities.
    
    Key Features:
    - Comprehensive result lifecycle management from initialization to completion
    - Specialized processor coordination for performance, trade, and equity processing
    - Advanced JSON parsing and validation of C++ engine output
    - Result data structure validation and integrity checking
    - In-memory result storage with automatic cleanup capabilities
    - Error handling and status management throughout processing pipeline
    - Batch result management with retrieval and cleanup operations
    
    Processing Architecture:
    The ResultProcessor coordinates specialized processors (PerformanceCalculator,
    TradeConverter, EquityProcessor) to provide comprehensive result processing
    with validation, error handling, and quality assurance throughout the pipeline.
    
    Result Storage Management:
    The service maintains in-memory result storage with simulation lifecycle tracking,
    automatic cleanup of old results, comprehensive status management, and detailed
    error handling with error message storage for debugging and monitoring.
    """
    
    def __init__(self):
        """
        Initialize the ResultProcessor with specialized processors and result storage.
        
        The processor maintains an in-memory results storage system and initializes
        specialized processors for performance calculation, trade conversion, and
        equity processing to provide comprehensive result processing capabilities.
        """
        # In-memory result storage with simulation lifecycle tracking
        self.results_storage: Dict[str, SimulationResults] = {}
        
        # Initialize specialized processors for comprehensive result processing
        self.performance_calculator = PerformanceCalculator()
        self.trade_converter = TradeConverter()
        self.equity_processor = EquityProcessor()
    
    def initialize_simulation_result(self, simulation_id: str, config: SimulationConfig) -> SimulationResults:
        """
        Initialize a new simulation result with pending status and configuration.
        
        This method creates a new SimulationResults object with initial state and
        configuration, establishing the result lifecycle tracking and storage for
        the simulation. It sets up the result structure for subsequent processing
        and status updates throughout the simulation execution.
        
        Args:
            simulation_id: Unique identifier for the simulation
            config: SimulationConfig object containing simulation parameters
            
        Returns:
            SimulationResults: Initialized result object with pending status
            
        Result Initialization:
        The method creates a comprehensive result object with:
        - Simulation identification and configuration
        - Initial status set to PENDING
        - Timestamp tracking for lifecycle management
        - Empty containers for performance metrics and trades
        - Error handling preparation
        
        The initialized result is stored in the results storage for lifecycle
        management and subsequent processing operations.
        """
        # Create comprehensive simulation result with initial state
        result = SimulationResults(
            simulation_id=simulation_id,
            status=SimulationStatus.PENDING,
            config=config,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            performance_metrics=None,
            trades=[],
            error_message=None
        )
        
        # Store result for lifecycle management and processing
        self.results_storage[simulation_id] = result
        return result
    
    def update_simulation_status(self, simulation_id: str, status: SimulationStatus, 
                               started_at: Optional[datetime] = None):
        """
        Update simulation status and lifecycle timestamps.
        
        This method updates the status of a simulation and optionally sets the
        started_at timestamp for lifecycle tracking. It provides safe status
        updates with validation and error handling for unknown simulations.
        
        Args:
            simulation_id: Unique identifier for the simulation
            status: New simulation status to set
            started_at: Optional timestamp for when simulation started
            
        Status Management:
        The method safely updates simulation status with validation for existing
        simulations and provides appropriate logging for unknown simulation IDs.
        It maintains accurate lifecycle timestamps for monitoring and analysis.
        """
        if simulation_id not in self.results_storage:
            logger.warning(f"Attempting to update status for unknown simulation: {simulation_id}")
            return
        
        # Update simulation status and lifecycle timestamps
        self.results_storage[simulation_id].status = status
        if started_at:
            self.results_storage[simulation_id].started_at = started_at
    
    def process_simulation_results(self, simulation_id: str, result_data: Dict[str, Any]):
        """
        Comprehensive processing of simulation results using specialized processors.
        
        This method coordinates the complete result processing pipeline, transforming
        raw C++ engine output into structured SimulationResults objects. It orchestrates
        multiple specialized processors to handle performance metrics, trade conversion,
        equity processing, and additional result data processing.
        
        Args:
            simulation_id: Unique identifier for the simulation
            result_data: Dictionary containing raw C++ engine simulation output
            
        Processing Pipeline:
        1. Validate simulation existence and retrieve result object
        2. Update completion status and timestamps
        3. Process basic financial results from C++ engine
        4. Calculate performance metrics using PerformanceCalculator
        5. Convert trading signals to trade records using TradeConverter
        6. Process equity curve data using EquityProcessor
        7. Handle optional data (memory statistics, optimization info)
        8. Complete processing with success logging
        
        The method provides comprehensive error handling that catches processing
        failures and marks simulations as failed with detailed error messages.
        
        Specialized Processor Coordination:
        The method coordinates specialized processors to ensure comprehensive
        result processing with validation, error handling, and quality assurance
        throughout the processing pipeline.
        """
        if simulation_id not in self.results_storage:
            logger.error(f"Cannot process results for unknown simulation: {simulation_id}")
            return
        
        try:
            # Retrieve simulation result for comprehensive processing
            simulation_result = self.results_storage[simulation_id]
            
            # Update completion status and timestamp
            simulation_result.status = SimulationStatus.COMPLETED
            simulation_result.completed_at = datetime.now()
            
            # Process basic financial results from C++ engine output
            simulation_result.starting_capital = result_data.get("starting_capital")
            simulation_result.ending_value = result_data.get("ending_value")
            simulation_result.total_return_pct = result_data.get("total_return_pct")
            
            # Process performance metrics using specialized calculator
            simulation_result.performance_metrics = self.performance_calculator.calculate_performance_metrics(result_data)
            
            # Process trading signals into structured trade records using specialized converter
            signals_data = result_data.get("signals", [])
            simulation_result.trades = self.trade_converter.convert_signals_to_trades(signals_data, result_data)
            
            # Process equity curve data using specialized processor
            simulation_result.equity_curve = self.equity_processor.process_equity_curve(result_data)
            
            # Process optional memory statistics if available from C++ engine
            if "memory_statistics" in result_data:
                simulation_result.memory_statistics = result_data["memory_statistics"]
                logger.debug(f"Memory statistics added for simulation {simulation_id}")
            
            # Process optional optimization information if available
            if "optimization_info" in result_data:
                simulation_result.optimization_info = result_data["optimization_info"]
                logger.debug(f"Optimization info added for simulation {simulation_id}")
            
            logger.info(f"Successfully processed results for simulation {simulation_id}")
            
        except Exception as e:
            logger.error(f"Error processing simulation results for {simulation_id}: {e}")
            self.mark_simulation_failed(simulation_id, f"Result processing error: {str(e)}")
    
    def mark_simulation_failed(self, simulation_id: str, error_message: str):
        """
        Mark simulation as failed with error message and completion timestamp.
        
        This method updates the simulation status to FAILED, records the error
        message for debugging, and sets the completion timestamp for lifecycle
        tracking. It provides comprehensive error handling and logging for
        failed simulations.
        
        Args:
            simulation_id: Unique identifier for the simulation
            error_message: Detailed error message describing the failure
            
        Failure Handling:
        The method safely updates simulation status with validation for existing
        simulations and provides detailed error logging for monitoring and
        debugging purposes. It maintains accurate lifecycle timestamps and
        error information for analysis.
        """
        if simulation_id not in self.results_storage:
            logger.warning(f"Attempting to mark unknown simulation as failed: {simulation_id}")
            return
        
        # Update simulation status to failed with error details and completion timestamp
        self.results_storage[simulation_id].status = SimulationStatus.FAILED
        self.results_storage[simulation_id].error_message = error_message
        self.results_storage[simulation_id].completed_at = datetime.now()
        
        logger.error(f"Simulation {simulation_id} marked as failed: {error_message}")
    
    def get_simulation_result(self, simulation_id: str) -> Optional[SimulationResults]:
        """
        Retrieve simulation result by ID.
        
        This method provides safe access to simulation results with None return
        for unknown simulation IDs. It enables result retrieval for analysis,
        monitoring, and API response generation.
        
        Args:
            simulation_id: Unique identifier for the simulation
            
        Returns:
            Optional[SimulationResults]: Simulation result object or None if not found
        """
        return self.results_storage.get(simulation_id)
    
    def get_all_simulation_results(self) -> Dict[str, SimulationResults]:
        """
        Retrieve all simulation results as a dictionary copy.
        
        This method provides batch access to all stored simulation results,
        returning a copy to prevent external modification of internal storage.
        It enables comprehensive result analysis and monitoring capabilities.
        
        Returns:
            Dict[str, SimulationResults]: Copy of all simulation results
        """
        return self.results_storage.copy()
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """
        Clean up old simulation results based on configurable age threshold.
        
        This method removes simulation results that exceed the specified age
        threshold to manage memory usage and maintain system performance. It
        provides configurable cleanup with detailed logging for monitoring.
        
        Args:
            max_age_hours: Maximum age in hours before results are removed (default: 24)
            
        Returns:
            int: Number of results removed during cleanup
            
        Cleanup Process:
        1. Calculate cutoff time based on age threshold
        2. Identify results older than cutoff time
        3. Remove old results from storage
        4. Log cleanup operations for monitoring
        5. Return count of removed results
        
        The method provides resource management for long-running systems by
        automatically cleaning up old results while maintaining configurable
        retention policies.
        """
        # Calculate cutoff time for result cleanup
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Identify results older than cutoff time for removal
        to_remove = []
        for simulation_id, result in self.results_storage.items():
            if result.created_at < cutoff_time:
                to_remove.append(simulation_id)
        
        # Remove old results from storage with logging
        for simulation_id in to_remove:
            del self.results_storage[simulation_id]
            logger.info(f"Cleaned up old simulation result: {simulation_id}")
        
        return len(to_remove)
    
    
    def parse_json_result(self, json_text: str) -> Dict[str, Any]:
        """
        Parse and validate JSON result from C++ engine with comprehensive error handling.
        
        This method provides robust JSON parsing for C++ engine output with
        comprehensive validation, error detection, and corruption handling.
        It implements multi-stage validation to ensure data integrity and
        provide detailed error information for debugging.
        
        Args:
            json_text: Raw JSON text from C++ engine output
            
        Returns:
            Dict[str, Any]: Parsed and validated JSON data
            
        Raises:
            json.JSONDecodeError: If JSON parsing fails or validation errors occur
            
        Parsing Pipeline:
        1. Empty output validation
        2. Pre-validation for common malformed JSON patterns
        3. JSON parsing with standard library
        4. Post-parse structure validation
        5. Comprehensive error handling and logging
        
        The method provides detailed error information for debugging and
        monitoring, enabling effective troubleshooting of C++ engine output
        issues and data corruption problems.
        """
        # Parse and validate JSON result from C++ engine with comprehensive error handling
        try:
            if not json_text.strip():
                raise json.JSONDecodeError("Empty output", "", 0)
            
            # Pre-validation: Check for common malformed JSON patterns and corruption
            self._pre_validate_json_text(json_text)
            
            # Parse JSON using standard library with error handling
            result_data = json.loads(json_text)
            
            # Post-parse validation for structure integrity
            self._validate_parsed_json_structure(result_data)
            
            return result_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON result: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON validation error: {e}")
            raise json.JSONDecodeError(str(e), json_text, 0)
    
    def validate_result_data(self, result_data: Dict[str, Any]) -> bool:
        """
        Comprehensive validation of C++ engine result data structure and content.
        
        This method performs thorough validation of simulation result data using
        a combination of basic field validation, specialized processor validation,
        and cross-field consistency checking. It coordinates multiple validation
        layers to ensure data integrity and quality.
        
        Args:
            result_data: Dictionary containing simulation result data from C++ engine
            
        Returns:
            bool: True if all validations pass, False otherwise
            
        Validation Pipeline:
        1. Required field validation (ending_value, starting_capital)
        2. Numeric field validation with type and constraint checking
        3. Performance metrics validation using PerformanceCalculator
        4. Trading signals validation using TradeConverter
        5. Equity curve validation using EquityProcessor
        6. Cross-field consistency validation
        
        The method provides comprehensive error logging for each validation
        failure, enabling precise debugging and data quality monitoring.
        
        Specialized Processor Validation:
        The method leverages specialized processors for domain-specific validation,
        ensuring comprehensive data quality checking across all result components.
        """
        # Comprehensive validation of C++ engine result data structure and content
        try:
            # Validate presence of basic required fields
            required_fields = ["ending_value", "starting_capital"]
            for field in required_fields:
                if field not in result_data:
                    logger.error(f"Missing required field in result data: {field}")
                    return False
            
            # Validate numeric fields with type and constraint checking
            numeric_validations = [
                ("ending_value", float, lambda x: x >= 0),
                ("starting_capital", float, lambda x: x > 0),
                ("total_return_pct", float, None),  # Can be negative (losses)
            ]
            
            for field, _, validator in numeric_validations:
                if field in result_data:
                    value = result_data[field]
                    if not isinstance(value, (int, float)):
                        logger.error(f"Field '{field}' must be numeric, got {type(value)}")
                        return False
                    if validator and not validator(value):
                        logger.error(f"Field '{field}' failed validation: {value}")
                        return False
            
            # Validate performance metrics structure using specialized calculator
            if "performance_metrics" in result_data:
                if not self.performance_calculator.validate_performance_metrics(result_data["performance_metrics"]):
                    return False
            
            # Validate trading signals structure using specialized converter
            if "signals" in result_data:
                if not self.trade_converter.validate_signals(result_data["signals"]):
                    return False
            
            # Validate equity curve structure using specialized processor
            if "equity_curve" in result_data:
                if not self.equity_processor.validate_equity_curve(result_data["equity_curve"]):
                    return False
            
            # Cross-field consistency validation using specialized calculator
            if not self.performance_calculator.validate_cross_field_consistency(result_data):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Exception during result data validation: {e}")
            return False
    
    def _pre_validate_json_text(self, json_text: str):
        """
        Lightweight pre-validation checks for obvious JSON corruption and errors.
        
        This private method performs quick validation checks on raw JSON text to
        identify common corruption patterns, C++ runtime errors, and structural
        issues before attempting JSON parsing. It provides early error detection
        to prevent parsing failures and provide better error messages.
        
        Args:
            json_text: Raw JSON text to validate
            
        Raises:
            ValueError: If corruption or structural issues are detected
            
        Validation Checks:
        1. C++ runtime error detection (segmentation faults, exceptions)
        2. Incomplete JSON detection (missing start/end markers)
        3. Error message detection in output
        4. Brace and bracket balance validation
        
        The method provides early detection of common C++ engine failure modes
        and output corruption, enabling better error handling and debugging.
        """
        # Lightweight pre-validation checks for obvious JSON corruption
        
        # Check for C++ runtime errors in output that indicate engine crashes
        if "terminate called" in json_text or "segmentation fault" in json_text:
            raise ValueError("JSON contains C++ runtime error messages")
        
        # Check for incomplete JSON (common with crashed processes)
        if not json_text.strip().startswith('{'):
            if any(error_indicator in json_text.lower() for error_indicator in 
                   ["error:", "exception:", "failed:", "abort", "crash"]):
                raise ValueError("Output contains error messages instead of JSON")
        
        # Simple brace/bracket balance check for structural integrity
        brace_count = json_text.count('{') - json_text.count('}')
        bracket_count = json_text.count('[') - json_text.count(']')
        
        if brace_count != 0:
            raise ValueError(f"Unbalanced braces in JSON (difference: {brace_count})")
        if bracket_count != 0:
            raise ValueError(f"Unbalanced brackets in JSON (difference: {bracket_count})")
    
    def _validate_parsed_json_structure(self, result_data: Dict[str, Any]):
        """
        Validate the basic structure of parsed JSON data from C++ engine.
        
        This private method performs structural validation of parsed JSON data
        to ensure it meets basic requirements for result processing. It validates
        the root structure, checks for corruption indicators, and ensures critical
        fields are not null or undefined.
        
        Args:
            result_data: Parsed JSON data to validate
            
        Raises:
            ValueError: If structural issues or corruption are detected
            
        Validation Checks:
        1. Root object type validation (must be dictionary)
        2. Empty object detection
        3. Key type validation (must be strings)
        4. Critical field null value detection
        
        The method provides structural integrity validation for parsed JSON
        data, ensuring it can be safely processed by subsequent validation
        and processing stages.
        """
        # Validate the basic structure of parsed JSON data
        if not isinstance(result_data, dict):
            raise ValueError(f"Root JSON must be object/dict, got {type(result_data)}")
        
        if len(result_data) == 0:
            raise ValueError("JSON object is empty")
        
        # Check for obvious corruption indicators in JSON structure
        for key, value in result_data.items():
            if not isinstance(key, str):
                raise ValueError(f"JSON key must be string, got {type(key)}: {key}")
            
            # Check for null/undefined values in critical fields
            if value is None and key in ["ending_value", "starting_capital"]:
                raise ValueError(f"Critical field '{key}' is null")