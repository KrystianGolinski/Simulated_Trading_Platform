import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .error_types import SimulationError, ErrorCode, ErrorSeverity
from .error_categorizers import (
    ErrorCategorizer, TimeoutErrorCategorizer, PermissionErrorCategorizer,
    MemoryErrorCategorizer, DiskSpaceErrorCategorizer, FileNotFoundErrorCategorizer,
    GenericErrorCategorizer, CppErrorExtractor
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self):
        self.error_history: List[SimulationError] = []
        self.cpp_error_extractor = CppErrorExtractor()
        self.categorizers: List[ErrorCategorizer] = [
            TimeoutErrorCategorizer(),
            FileNotFoundErrorCategorizer(),
            PermissionErrorCategorizer(),
            DiskSpaceErrorCategorizer(),
            MemoryErrorCategorizer(),
            GenericErrorCategorizer()  # Must be last as it's the fallback
        ]
    
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
            "cpp_error_details": self.cpp_error_extractor.extract_cpp_error_details(stderr, stdout)
        }
        
        # Use strategy pattern to find appropriate categorizer
        for categorizer in self.categorizers:
            if categorizer.can_handle(return_code, stdout, stderr):
                error = categorizer.categorize(return_code, stdout, stderr, context)
                self._log_error(error)
                return error
        
        # This should never happen as GenericErrorCategorizer handles everything
        error = SimulationError(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message="Unknown error occurred",
            severity=ErrorSeverity.MEDIUM,
            context=context
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
    
