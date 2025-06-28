import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .error_types import SimulationError, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)

class ErrorCategorizer(ABC):
    @abstractmethod
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        pass
    
    @abstractmethod
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
        pass

class TimeoutErrorCategorizer(ErrorCategorizer):
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return return_code == -9 or "killed" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
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
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return "permission denied" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
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
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return "out of memory" in stderr.lower() or "bad_alloc" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
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
    def can_handle(self, return_code: int, stdout: str, stderr: str) -> bool:
        return "no space left" in stderr.lower()
    
    def categorize(self, return_code: int, stdout: str, stderr: str, context: Dict[str, Any]) -> SimulationError:
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
    def __init__(self):
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
    def extract_cpp_error_details(self, stderr: str, stdout: str) -> Dict[str, Any]:
        # Extract detailed C++ error information from stderr and stdout
        
        details = {
            "exception_type": None,
            "error_message": None,
            "file_location": None,
            "line_number": None,
            "function_name": None,
            "stack_trace": None,
            "suggestions": []
        }
        
        # Combine stderr and stdout for comprehensive error analysis
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