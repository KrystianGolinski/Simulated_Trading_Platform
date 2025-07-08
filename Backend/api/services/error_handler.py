# Error Handler - Comprehensive Error Management and Analysis System
# This module provides advanced error handling capabilities for the Trading Platform API
# 
# Architecture Overview:
# The ErrorHandler implements a sophisticated error management system that coordinates
# multiple error categorizers to provide comprehensive error analysis, context preservation,
# and actionable resolution suggestions. It serves as the central hub for all error
# handling operations in the trading platform.
#
# Key Responsibilities:
# 1. Error categorization using strategy pattern with multiple specialized categorizers
# 2. Context preservation for debugging and monitoring
# 3. Error history tracking and statistical analysis
# 4. C++ engine error analysis and extraction
# 5. Validation error handling and processing
# 6. Severity-based logging and alerting
#
# Error Processing Pipeline:
# 1. Receive error information from various sources (C++ engine, validation, etc.)
# 2. Extract detailed context and C++ error patterns
# 3. Apply appropriate categorizer using chain of responsibility pattern
# 4. Generate comprehensive SimulationError with suggestions
# 5. Log error based on severity level
# 6. Track error in history for pattern analysis
#
# Integration with Trading Platform:
# - Central error processing hub for all simulation and API errors
# - Provides detailed error context for debugging and monitoring
# - Supports error pattern analysis for system health monitoring
# - Enables intelligent error recovery and user feedback
# - Integrates with logging and monitoring infrastructure
#
# Error Categorization Strategy:
# The handler uses a prioritized chain of categorizers:
# 1. TimeoutErrorCategorizer - Process timeout and termination errors
# 2. FileNotFoundErrorCategorizer - Missing executable or file errors
# 3. PermissionErrorCategorizer - File permission and access errors
# 4. DiskSpaceErrorCategorizer - Storage and disk space errors
# 5. MemoryErrorCategorizer - Memory allocation and out-of-memory errors
# 6. GenericErrorCategorizer - Fallback for unclassified errors with C++ analysis

import logging
from typing import Dict, Any, Optional, List
from .error_types import SimulationError, ErrorCode, ErrorSeverity
from .error_categorizers import (
    ErrorCategorizer, TimeoutErrorCategorizer, PermissionErrorCategorizer,
    MemoryErrorCategorizer, DiskSpaceErrorCategorizer, FileNotFoundErrorCategorizer,
    GenericErrorCategorizer, CppErrorExtractor
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Comprehensive Error Management and Analysis System for the Trading Platform.
    
    This class serves as the central hub for all error handling operations, providing
    sophisticated error categorization, context preservation, and resolution suggestions.
    It coordinates multiple specialized error categorizers and maintains error history
    for pattern analysis and system health monitoring.
    
    Key Features:
    - Chain of responsibility pattern for error categorization
    - Comprehensive C++ error analysis and extraction
    - Error history tracking and statistical analysis
    - Severity-based logging and alerting
    - Context preservation for debugging and monitoring
    - Actionable resolution suggestions for different error types
    
    Architecture:
    The ErrorHandler uses a prioritized chain of categorizers that are processed in order:
    1. TimeoutErrorCategorizer - Handles process timeouts and terminations
    2. FileNotFoundErrorCategorizer - Handles missing executables and files
    3. PermissionErrorCategorizer - Handles file permission and access errors
    4. DiskSpaceErrorCategorizer - Handles storage and disk space errors
    5. MemoryErrorCategorizer - Handles memory allocation and out-of-memory errors
    6. GenericErrorCategorizer - Fallback for unclassified errors with C++ analysis
    """
    
    def __init__(self):
        """
        Initialize the ErrorHandler with categorizers and error tracking.
        
        Sets up the error categorization chain, C++ error extractor, and
        error history tracking for comprehensive error management.
        """
        # Error history for pattern analysis and monitoring
        self.error_history: List[SimulationError] = []
        
        # C++ error analysis and extraction service
        self.cpp_error_extractor = CppErrorExtractor()
        
        # Prioritized chain of error categorizers
        # Order is important - more specific categorizers should come first
        self.categorizers: List[ErrorCategorizer] = [
            TimeoutErrorCategorizer(),          # Process timeout/termination errors
            FileNotFoundErrorCategorizer(),     # Missing executable errors
            PermissionErrorCategorizer(),       # File permission errors  
            DiskSpaceErrorCategorizer(),        # Storage/disk space errors
            MemoryErrorCategorizer(),           # Memory allocation errors
            GenericErrorCategorizer()           # Fallback categorizer (must be last)
        ]
    
    def create_engine_validation_error(self, validation_result: Dict[str, Any]) -> SimulationError:
        """
        Create a comprehensive error for C++ engine validation failures.
        
        This method handles errors that occur during C++ engine validation,
        such as missing executables, configuration issues, or permission problems.
        It maps validation result codes to appropriate error codes and provides
        contextual information for debugging.
        
        Args:
            validation_result: Dictionary containing validation error information
                - error_code: Validation error code
                - error: Error message
                - suggestions: List of resolution suggestions
                
        Returns:
            SimulationError: Comprehensive error object with categorization and suggestions
        """
        # Map validation error codes to internal error codes
        error_code_mapping = {
            'ENGINE_NOT_CONFIGURED': ErrorCode.ENGINE_NOT_CONFIGURED,
            'ENGINE_FILE_NOT_FOUND': ErrorCode.ENGINE_FILE_NOT_FOUND,
            'ENGINE_NOT_EXECUTABLE': ErrorCode.ENGINE_NOT_EXECUTABLE
        }
        
        # Resolve error code with fallback to unknown error
        error_code = error_code_mapping.get(
            validation_result.get('error_code'), 
            ErrorCode.UNKNOWN_ERROR
        )
        
        # Create comprehensive error object
        error = SimulationError(
            error_code=error_code,
            message=validation_result.get('error', 'Unknown engine validation error'),
            severity=ErrorSeverity.CRITICAL,  # Engine validation errors are critical
            suggestions=validation_result.get('suggestions', [])
        )
        
        # Log and track the error
        self._log_error(error)
        return error
    
    def categorize_cpp_engine_error(self, return_code: int, stdout: str, stderr: str) -> SimulationError:
        """
        Categorize and analyze C++ engine execution errors using specialized categorizers.
        
        This method serves as the main entry point for C++ engine error analysis.
        It constructs comprehensive context information, applies the chain of responsibility
        pattern to find the appropriate categorizer, and returns a detailed error object
        with actionable suggestions.
        
        Args:
            return_code: Process return code from C++ engine execution
            stdout: Standard output from the C++ engine
            stderr: Standard error output from the C++ engine
            
        Returns:
            SimulationError: Comprehensive error object with categorization, context, and suggestions
        """
        # Build comprehensive context for error analysis and debugging
        context = {
            "return_code": return_code,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr),
            "has_stdout": bool(stdout.strip()),
            "has_stderr": bool(stderr.strip()),
            # Preserve full error output for debugging (truncated if too long)
            "cpp_stdout": stdout.strip() if stdout.strip() else None,
            "cpp_stderr": stderr.strip() if stderr.strip() else None,
            # Extract detailed C++ error patterns and analysis
            "cpp_error_details": self.cpp_error_extractor.extract_cpp_error_details(stderr, stdout)
        }
        
        # Apply chain of responsibility pattern to find appropriate categorizer
        for categorizer in self.categorizers:
            if categorizer.can_handle(return_code, stdout, stderr):
                error = categorizer.categorize(return_code, stdout, stderr, context)
                self._log_error(error)
                return error
        
        # Fallback error (should never happen as GenericErrorCategorizer handles everything)
        error = SimulationError(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message="Unknown error occurred during C++ engine execution",
            severity=ErrorSeverity.MEDIUM,
            context=context,
            suggestions=["Contact support - error categorization failed"]
        )
        self._log_error(error)
        return error
    
    def create_json_parse_error(self, json_error: str, raw_output: str) -> SimulationError:
        error = SimulationError(
            error_code=ErrorCode.JSON_PARSE_ERROR,
            message=f"Failed to parse C++ engine output as JSON: {json_error}",
            severity=ErrorSeverity.MEDIUM,
            context={
                "json_error": json_error,
                "raw_output_preview": raw_output[:500] if raw_output else "",
                "output_length": len(raw_output)
            },
            suggestions=[
                "Check if C++ engine is producing valid JSON output",
                "Verify simulation completed successfully",
                "Review C++ engine output format"
            ]
        )
        
        self._log_error(error)
        return error
    
    def create_validation_error(self, validation_message: str, 
                              context: Optional[Dict[str, Any]] = None) -> SimulationError:
        error = SimulationError(
            error_code=ErrorCode.INVALID_RESULT_DATA,
            message=validation_message,
            severity=ErrorSeverity.MEDIUM,
            context=context or {},
            suggestions=[
                "Check simulation configuration",
                "Verify input data quality",
                "Review C++ engine output format"
            ]
        )
        
        self._log_error(error)
        return error
    
    def create_generic_error(self, message: str, 
                           context: Optional[Dict[str, Any]] = None,
                           severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> SimulationError:
        error = SimulationError(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message=message,
            severity=severity,
            context=context or {},
            suggestions=["Contact support if this error persists"]
        )
        
        self._log_error(error)
        return error
    
    def _log_error(self, error: SimulationError):
        self.error_history.append(error)
        
        # Log based on severity
        log_message = f"[{error.error_code.value}] {error.message}"
        if error.context:
            log_message += f" | Context: {error.context}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive error statistics for monitoring and analysis.
        
        This method provides detailed statistics about error patterns, frequency,
        and severity distribution for system health monitoring and debugging.
        It's useful for identifying recurring issues and system reliability metrics.
        
        Returns:
            Dict[str, Any]: Comprehensive error statistics containing:
                - total_errors: Total number of errors tracked
                - error_codes: Frequency count of each error code
                - severity_distribution: Distribution of errors by severity level
                - latest_error: Most recent error details (if any)
        """
        if not self.error_history:
            return {"total_errors": 0}
        
        # Count occurrences of each error code
        error_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            error_counts[error.error_code.value] = error_counts.get(error.error_code.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_codes": error_counts,
            "severity_distribution": severity_counts,
            "latest_error": self.error_history[-1].to_dict() if self.error_history else None
        }
    
    def clear_error_history(self):
        self.error_history.clear()
        logger.info("Error history cleared")
    
