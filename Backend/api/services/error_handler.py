import logging
import re
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    # Engine errors
    ENGINE_NOT_CONFIGURED = "ENGINE_NOT_CONFIGURED"
    ENGINE_FILE_NOT_FOUND = "ENGINE_FILE_NOT_FOUND"
    ENGINE_NOT_EXECUTABLE = "ENGINE_NOT_EXECUTABLE"
    
    # Execution errors
    PROCESS_EXECUTION_FAILED = "PROCESS_EXECUTION_FAILED"
    PROCESS_TIMEOUT = "PROCESS_TIMEOUT"
    INVALID_WORKING_DIRECTORY = "INVALID_WORKING_DIRECTORY"
    
    # Data errors
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    INVALID_RESULT_DATA = "INVALID_RESULT_DATA"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    
    # Simulation errors
    SIMULATION_NOT_FOUND = "SIMULATION_NOT_FOUND"
    SIMULATION_ALREADY_RUNNING = "SIMULATION_ALREADY_RUNNING"
    INVALID_SIMULATION_CONFIG = "INVALID_SIMULATION_CONFIG"
    
    # System errors
    MEMORY_ERROR = "MEMORY_ERROR"
    DISK_SPACE_ERROR = "DISK_SPACE_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    
    # Unknown error
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SimulationError:
    def __init__(self, error_code: ErrorCode, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[List[str]] = None):
        self.error_code = error_code
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }

class ErrorHandler:
    def __init__(self):
        self.error_history: List[SimulationError] = []
    
    def create_engine_validation_error(self, validation_result: Dict[str, Any]) -> SimulationError:
        error_code_mapping = {
            'ENGINE_NOT_CONFIGURED': ErrorCode.ENGINE_NOT_CONFIGURED,
            'ENGINE_FILE_NOT_FOUND': ErrorCode.ENGINE_FILE_NOT_FOUND,
            'ENGINE_NOT_EXECUTABLE': ErrorCode.ENGINE_NOT_EXECUTABLE
        }
        
        error_code = error_code_mapping.get(
            validation_result.get('error_code'), 
            ErrorCode.UNKNOWN_ERROR
        )
        
        error = SimulationError(
            error_code=error_code,
            message=validation_result.get('error', 'Unknown engine validation error'),
            severity=ErrorSeverity.CRITICAL,
            suggestions=validation_result.get('suggestions', [])
        )
        
        self._log_error(error)
        return error
    
    def categorize_cpp_engine_error(self, return_code: int, stdout: str, stderr: str) -> SimulationError:
        # Enhanced context preservation - capture full C++ error details
        context = {
            "return_code": return_code,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr),
            "has_stdout": bool(stdout.strip()),
            "has_stderr": bool(stderr.strip()),
            # Preserve full error output for debugging
            "cpp_stdout": stdout.strip() if stdout.strip() else None,
            "cpp_stderr": stderr.strip() if stderr.strip() else None,
            # Extract C++ specific error patterns
            "cpp_error_details": self._extract_cpp_error_details(stderr, stdout)
        }
        
        # Categorize based on return code and error content
        if return_code == -9 or "killed" in stderr.lower():
            error = SimulationError(
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
        elif return_code == 127:
            error = SimulationError(
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
        elif "permission denied" in stderr.lower():
            error = SimulationError(
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
        elif "no space left" in stderr.lower():
            error = SimulationError(
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
        elif "out of memory" in stderr.lower() or "bad_alloc" in stderr.lower():
            error = SimulationError(
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
        else:
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
            
            error = SimulationError(
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
        if not self.error_history:
            return {"total_errors": 0}
        
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
    
    def _extract_cpp_error_details(self, stderr: str, stdout: str) -> Dict[str, Any]:
        """Extract detailed C++ error information from stderr and stdout."""
        
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