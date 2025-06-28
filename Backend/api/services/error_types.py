from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

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