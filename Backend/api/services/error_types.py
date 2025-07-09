# Error Types - Comprehensive Error Classification and Data Models
# This module defines the core error classification system for the Trading Platform API
#
# Architecture Overview:
# The error types module implements a comprehensive error classification framework that
# provides standardized error codes, severity levels, and error data structures for
# the entire trading platform. It ensures consistent error handling and reporting
# across all components of the system.
#
# Key Components:
# 1. ErrorCode - Comprehensive enumeration of all possible error conditions
# 2. ErrorSeverity - Classification system for error severity levels
# 3. SimulationError - Rich error data model with context and suggestions
#
# Error Classification Framework:
# The system categorizes errors into logical groups:
# - Engine Errors: C++ engine configuration and validation issues
# - Execution Errors: Process execution and runtime failures
# - Data Errors: JSON parsing and data validation issues
# - Simulation Errors: Simulation-specific configuration and state issues
# - System Errors: Infrastructure and resource-related failures
#
# Severity Classification:
# - LOW: Informational issues that don't affect functionality
# - MEDIUM: Warnings and recoverable errors
# - HIGH: Serious errors that affect functionality
# - CRITICAL: Fatal errors that prevent system operation
#
# Integration with Trading Platform:
# - Provides standardized error codes for consistent error handling
# - Supports error severity classification for appropriate response handling
# - Enables comprehensive error context preservation for debugging
# - Facilitates error pattern analysis and system health monitoring
# - Supports actionable error resolution suggestions

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorCode(Enum):
    """
    Comprehensive enumeration of all error conditions in the Trading Platform.

    This enumeration provides standardized error codes organized by category
    to ensure consistent error identification and handling across the platform.
    Each error code is designed to be machine-readable while remaining
    human-understandable for debugging and monitoring purposes.
    """

    # Engine Errors - C++ engine configuration and validation issues
    ENGINE_NOT_CONFIGURED = "ENGINE_NOT_CONFIGURED"  # Engine path not set or configured
    ENGINE_FILE_NOT_FOUND = "ENGINE_FILE_NOT_FOUND"  # Engine executable missing
    ENGINE_NOT_EXECUTABLE = (
        "ENGINE_NOT_EXECUTABLE"  # Engine file lacks execute permissions
    )

    # Execution Errors - Process execution and runtime failures
    PROCESS_EXECUTION_FAILED = (
        "PROCESS_EXECUTION_FAILED"  # General process execution failure
    )
    PROCESS_TIMEOUT = "PROCESS_TIMEOUT"  # Process killed due to timeout
    INVALID_WORKING_DIRECTORY = (
        "INVALID_WORKING_DIRECTORY"  # Invalid or inaccessible working directory
    )

    # Data Errors - JSON parsing and data validation issues
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"  # Failed to parse JSON output
    INVALID_RESULT_DATA = "INVALID_RESULT_DATA"  # Result data failed validation
    MISSING_REQUIRED_FIELDS = (
        "MISSING_REQUIRED_FIELDS"  # Required fields missing from data
    )

    # Simulation Errors - Simulation-specific configuration and state issues
    SIMULATION_NOT_FOUND = "SIMULATION_NOT_FOUND"  # Requested simulation doesn't exist
    SIMULATION_ALREADY_RUNNING = (
        "SIMULATION_ALREADY_RUNNING"  # Simulation already in progress
    )
    INVALID_SIMULATION_CONFIG = (
        "INVALID_SIMULATION_CONFIG"  # Invalid simulation configuration
    )

    # System Errors - Infrastructure and resource-related failures
    MEMORY_ERROR = "MEMORY_ERROR"  # Out of memory or memory allocation failure
    DISK_SPACE_ERROR = "DISK_SPACE_ERROR"  # Insufficient disk space
    PERMISSION_ERROR = "PERMISSION_ERROR"  # File or directory permission denied

    # Unknown Error - Fallback for unclassified errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"  # Unclassified or unexpected error


class ErrorSeverity(Enum):
    """
    Error severity classification system for the Trading Platform.

    This enumeration provides a standardized way to classify error severity
    levels, enabling appropriate response handling, logging levels, and
    alerting mechanisms based on the impact of the error.

    Severity Levels:
    - LOW: Informational issues that don't affect functionality
    - MEDIUM: Warnings and recoverable errors that may affect performance
    - HIGH: Serious errors that significantly affect functionality
    - CRITICAL: Fatal errors that prevent system operation
    """

    LOW = "low"  # Informational issues, no functional impact
    MEDIUM = "medium"  # Warnings and recoverable errors
    HIGH = "high"  # Serious errors affecting functionality
    CRITICAL = "critical"  # Fatal errors preventing operation


class SimulationError:
    """
    Comprehensive error data model for the Trading Platform.

    This class provides a rich error representation that includes detailed context,
    actionable suggestions, and comprehensive metadata for debugging and monitoring.
    It serves as the primary error data structure throughout the platform.

    Key Features:
    - Standardized error code classification
    - Severity-based error categorization
    - Rich context preservation for debugging
    - Actionable resolution suggestions
    - Automatic timestamp tracking
    - Serializable data structure for API responses

    The SimulationError class is designed to capture comprehensive information
    about errors, enabling effective debugging, monitoring, and user feedback.
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        """
        Initialize a comprehensive simulation error with full context and suggestions.

        Args:
            error_code: Standardized error code from ErrorCode enumeration
            message: Human-readable error message describing the issue
            severity: Error severity level for appropriate response handling
            context: Optional dictionary containing detailed error context and debugging information
            suggestions: Optional list of actionable suggestions for error resolution

        The constructor automatically captures the current timestamp for error tracking
        and monitoring purposes. Context and suggestions default to empty containers
        if not provided.
        """
        self.error_code = error_code
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error object to a dictionary for API serialization.

        This method provides a standardized dictionary representation of the error
        that can be serialized to JSON for API responses. It includes all error
        information in a structured format suitable for client consumption.

        Returns:
            Dict[str, Any]: Complete error information including:
                - error_code: String representation of the error code
                - message: Human-readable error message
                - severity: String representation of severity level
                - context: Full context dictionary for debugging
                - suggestions: List of actionable resolution suggestions
                - timestamp: ISO-formatted timestamp of error occurrence

        The dictionary format ensures consistent error representation across
        all API endpoints and enables easy integration with monitoring systems.
        """
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
        }
