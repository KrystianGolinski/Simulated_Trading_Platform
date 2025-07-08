# Error Categorizers - Advanced Error Classification and Analysis System
# This module provides sophisticated error categorization and analysis for the Trading Platform API
# 
# Architecture Overview:
# The error categorizers implement a strategy pattern for classifying and handling different types
# of errors that can occur during simulation execution. Each categorizer specializes in a specific
# error type, providing detailed analysis, context preservation, and actionable resolution suggestions.
#
# Key Components:
# 1. ErrorCategorizer - Abstract base class defining the categorization interface
# 2. Specialized Categorizers - Handle specific error types (timeout, permission, memory, etc.)
# 3. CppErrorExtractor - Advanced C++ error analysis and pattern matching
# 4. GenericErrorCategorizer - Fallback categorizer for unclassified errors
#
# Error Classification Strategy:
# The system uses a chain of responsibility pattern where each categorizer:
# - Checks if it can handle the specific error type
# - Provides detailed categorization with context preservation
# - Offers specific suggestions for error resolution
# - Maintains error severity classification for appropriate response handling
#
# C++ Engine Integration:
# Special focus on C++ engine error analysis including:
# - Exception type detection and classification
# - Stack trace extraction and analysis
# - Memory and resource error identification
# - File and permission error handling
# - JSON parsing and database error detection
#
# Integration with Trading Platform:
# - Provides detailed error context for debugging and monitoring
# - Supports error pattern analysis for system health monitoring
# - Enables intelligent error handling and user feedback
# - Facilitates automated error recovery and suggestion generation

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any
from .error_types import SimulationError, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)

class ErrorCategorizer(ABC):
    """
    Abstract base class for error categorization strategies.
    
    This class defines the interface for error categorizers that implement the strategy pattern
    for handling different types of errors in the trading platform. Each concrete categorizer
    specializes in a specific error type and provides detailed analysis and resolution suggestions.
    
    The categorization process involves:
    1. Checking if the categorizer can handle the specific error type
    2. Analyzing the error context and extracting relevant information
    3. Creating a comprehensive SimulationError with appropriate severity and suggestions
    4. Preserving context information for debugging and monitoring
    """
    
    @abstractmethod
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        """
        Determine if this categorizer can handle the given error.
        
        Args:
            return_code: Process return code from C++ engine execution
            stdout: Standard output from the C++ engine
            stderr: Standard error output from the C++ engine
            
        Returns:
            bool: True if this categorizer can handle the error, False otherwise
        """
        pass
    
    @abstractmethod
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        """
        Categorize the error and create a comprehensive SimulationError object.
        
        Args:
            return_code: Process return code from C++ engine execution
            stdout: Standard output from the C++ engine
            stderr: Standard error output from the C++ engine
            context: Additional context information for error analysis
            
        Returns:
            SimulationError: Comprehensive error object with categorization, context, and suggestions
        """
        pass

class TimeoutErrorCategorizer(ErrorCategorizer):
    """
    Specialized categorizer for process timeout and termination errors.
    
    This categorizer handles errors that occur when the C++ engine process is terminated
    due to timeout or resource limits. It identifies both explicit timeout signals and
    process termination patterns in the error output.
    
    Common scenarios handled:
    - Process killed by timeout (return code -9)
    - Process terminated by system resource limits
    - Docker container resource limit enforcement
    """
    
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        """
        Check if the error indicates a timeout or process termination.
        
        Identifies timeout errors by checking for:
        - Return code -9 (SIGKILL signal)
        - "killed" keyword in stderr output
        
        Args:
            return_code: Process return code (-9 indicates SIGKILL)
            stdout: Standard output (not used for timeout detection)
            stderr: Standard error output (checked for "killed" keyword)
            
        Returns:
            bool: True if this is a timeout/termination error
        """
        return return_code == -9 or "killed" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        """
        Create a comprehensive timeout error with actionable suggestions.
        
        Args:
            return_code: Process return code
            stdout: Standard output from the process
            stderr: Standard error output from the process
            context: Additional context information
            
        Returns:
            SimulationError: Categorized timeout error with resolution suggestions
        """
        return SimulationError(
            error_code=ErrorCode.PROCESS_TIMEOUT,
            message="Simulation process was terminated (likely timeout or memory limit)",
            severity=ErrorSeverity.HIGH,
            context=context,
            suggestions=[
                "Check if simulation parameters are too resource-intensive",
                "Consider reducing date range or complexity",
                "Monitor Docker container resource limits"
            ]
        )

class PermissionErrorCategorizer(ErrorCategorizer):
    """
    Specialized categorizer for file permission and access errors.
    
    This categorizer handles errors that occur when the system cannot access
    or execute files due to permission restrictions. Common in containerized
    environments where file permissions need proper configuration.
    """
    
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        """Check if the error indicates a permission problem."""
        return "permission denied" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        """Create a comprehensive permission error with resolution suggestions."""
        return SimulationError(
            error_code=ErrorCode.PERMISSION_ERROR,
            message="Permission denied when executing C++ engine",
            severity=ErrorSeverity.HIGH,
            context=context,
            suggestions=[
                "Check file permissions on C++ engine",
                "Verify Docker container permissions",
                "Ensure proper user/group configuration"
            ]
        )

class MemoryErrorCategorizer(ErrorCategorizer):
    """
    Specialized categorizer for memory-related errors.
    
    This categorizer handles errors that occur when the C++ engine runs out of memory,
    such as `std::bad_alloc` exceptions.
    """
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        """Check if the error indicates an out-of-memory problem."""
        return "out of memory" in stderr.lower() or "bad_alloc" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        """Create a comprehensive memory error with resolution suggestions."""
        return SimulationError(
            error_code=ErrorCode.MEMORY_ERROR,
            message="Simulation ran out of memory",
            severity=ErrorSeverity.HIGH,
            context=context,
            suggestions=[
                "Reduce simulation complexity or date range",
                "Increase Docker container memory limits",
                "Optimize C++ engine memory usage"
            ]
        )

class DiskSpaceErrorCategorizer(ErrorCategorizer):
    """
    Specialized categorizer for disk space errors.
    
    This categorizer handles errors that occur when the system runs out of disk space,
    which can happen if the simulation generates a large amount of data.
    """
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        """Check if the error indicates a disk space problem."""
        return "no space left" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        """Create a comprehensive disk space error with resolution suggestions."""
        return SimulationError(
            error_code=ErrorCode.DISK_SPACE_ERROR,
            message="Insufficient disk space for simulation",
            severity=ErrorSeverity.HIGH,
            context=context,
            suggestions=[
                "Free up disk space",
                "Check Docker volume space limits",
                "Clean up old simulation data"
            ]
        )

class FileNotFoundErrorCategorizer(ErrorCategorizer):
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return return_code == 127
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        return SimulationError(
            error_code=ErrorCode.ENGINE_FILE_NOT_FOUND,
            message="C++ engine executable not found or not executable",
            severity=ErrorSeverity.CRITICAL,
            context=context,
            suggestions=[
                "Verify C++ engine was compiled successfully",
                "Check Docker volume mounts",
                "Ensure executable permissions are set"
            ]
        )

class GenericErrorCategorizer(ErrorCategorizer):
    """
    Fallback categorizer for unclassified errors.
    
    This categorizer is intended to be the last in the chain of responsibility,
    handling any errors not caught by more specific categorizers. It uses the
    `CppErrorExtractor` to provide as much detail as possible about the error.
    """
    def __init__(self):
        """
        Initialize the GenericErrorCategorizer.
        
        This categorizer serves as a fallback for errors that are not handled by
        more specific categorizers. It uses a CppErrorExtractor to analyze the
        error output for more detailed information.
        """
        self.cpp_error_extractor = CppErrorExtractor()
    
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return True  # This is the fallback categorizer
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        # Generic process execution failure with detailed C++ error preservation
        error_message = f"C++ engine failed with return code {return_code}"
        
        # Include detailed C++ error information in the message
        cpp_details = context.get("cpp_error_details", {})
        if cpp_details.get("exception_type"):
            error_message += f" - {cpp_details['exception_type']}"
        if cpp_details.get("error_message"):
            error_message += f": {cpp_details['error_message']}"
        elif stderr.strip():
            error_message += f": {stderr.strip()[:200]}"
        
        return SimulationError(
            error_code=ErrorCode.PROCESS_EXECUTION_FAILED,
            message=error_message,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            suggestions=[
                "Check simulation parameters for validity",
                "Review detailed C++ error output in error context",
                "Verify input data integrity",
                *cpp_details.get("suggestions", [])
            ]
        )

class CppErrorExtractor:
    """
    Advanced C++ error analysis and pattern extraction service.
    
    This class provides sophisticated analysis of C++ engine error output,
    extracting detailed information about exceptions, stack traces, and
    error patterns. It supports intelligent error categorization and
    provides context-specific suggestions for error resolution.
    
    Key Features:
    - Exception type detection and classification
    - Stack trace extraction and analysis
    - File location and line number identification
    - Context-specific suggestion generation
    - Memory, segmentation, and assertion error handling
    - JSON and database error detection
    """
    
    def extract_cpp_error_details(self, stderr: str, stdout: str) -> Dict[str, Any]:
        """
        Extract comprehensive C++ error information from process output.
        
        This method analyzes both stderr and stdout to extract detailed information
        about C++ exceptions, including exception types, error messages, file locations,
        stack traces, and generates context-specific suggestions for error resolution.
        
        Args:
            stderr: Standard error output from the C++ engine
            stdout: Standard output from the C++ engine
            
        Returns:
            Dict[str, Any]: Comprehensive error details containing:
                - exception_type: Type of C++ exception (if identifiable)
                - error_message: Detailed error message
                - file_location: Source file where error occurred
                - line_number: Line number of the error
                - function_name: Function where error occurred
                - stack_trace: Full stack trace (if available)
                - suggestions: Context-specific resolution suggestions
        """
        
        details = {
            "exception_type": None,
            "error_message": None,
            "file_location": None,
            "line_number": None,
            "function_name": None,
            "stack_trace": None,
            "suggestions": []
        }
        
        # Combine stderr and stdout for error analysis
        combined_output = f"{stderr}\n{stdout}".strip()
        if not combined_output:
            return details
        
        # Pattern matching for common C++ error types
        cpp_error_patterns = [
            # Standard C++ exceptions
            (r"(std::\w+(?:::\w+)*)\s*[:\-]\s*(.+)", "exception_type", "error_message"),
            (r"terminate called after throwing an instance of '([^']+)'\s*what\(\):\s*(.+)", "exception_type", "error_message"),
            (r"Exception:\s*([^\n]+)", None, "error_message"),
            
            # File and line information
            (r"([^\s]+\.(?:cpp|h|hpp)):(\d+)", "file_location", "line_number"),
            (r"at\s+([^\s]+)\s*\(([^)]+)\)", "function_name", None),
            
            # Specific error messages
            (r"(bad_alloc|out of memory)", "exception_type", None),
            (r"(segmentation fault|segfault)", "exception_type", None),
            (r"(assertion failed|assert)", "exception_type", None),
            (r"(null pointer|nullptr)", "exception_type", None),
        ]
        
        for pattern, key1, key2 in cpp_error_patterns:
            match = re.search(pattern, combined_output, re.IGNORECASE | re.MULTILINE)
            if match:
                if key1 and match.group(1):
                    details[key1] = match.group(1).strip()
                if key2 and len(match.groups()) > 1 and match.group(2):
                    details[key2] = match.group(2).strip()
        
        # Extract stack trace if present
        stack_trace_match = re.search(r'(stack trace:|backtrace:)(.*?)(?=\n\n|\Z)', 
                                    combined_output, re.IGNORECASE | re.DOTALL)
        if stack_trace_match:
            details["stack_trace"] = stack_trace_match.group(2).strip()
        
        # Generate context-specific suggestions
        if details["exception_type"]:
            exception_type = details["exception_type"].lower()
            if "bad_alloc" in exception_type or "memory" in exception_type:
                details["suggestions"].extend([
                    "Reduce data size or simulation complexity",
                    "Check for memory leaks in C++ code",
                    "Increase available memory"
                ])
            elif "segmentation" in exception_type or "segfault" in exception_type:
                details["suggestions"].extend([
                    "Check for null pointer dereferences",
                    "Verify array bounds",
                    "Review memory management in C++ code"
                ])
            elif "assertion" in exception_type or "assert" in exception_type:
                details["suggestions"].extend([
                    "Check preconditions and input validation",
                    "Review assertion conditions in C++ code"
                ])
        
        # Look for JSON-related errors
        if "json" in combined_output.lower():
            details["suggestions"].append("Check JSON parsing/generation in C++ engine")
        
        # Look for database-related errors
        if any(db_keyword in combined_output.lower() for db_keyword in ["sqlite", "database", "sql"]):
            details["suggestions"].append("Check database connection and query execution")
        
        return details