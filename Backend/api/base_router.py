from functools import wraps
from typing import Callable, Type, Any, Dict, List, Optional, TypeVar
from fastapi import Depends, HTTPException, Request
import logging
from abc import ABC

from database import DatabaseManager, get_database
from response_models import StandardResponse, create_success_response, create_error_response, ApiError
from models import ValidationResult

T = TypeVar('T')

class CentralizedLogger:
    # Centralized logging system for API operations
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_request(self, endpoint: str, params: Dict[str, Any] = None):
        self.logger.info(f"Request to {endpoint}", extra={"params": params})
    
    def log_success(self, endpoint: str, data_count: Optional[int] = None):
        extra = {"endpoint": endpoint}
        if data_count is not None:
            extra["data_count"] = data_count
        self.logger.info(f"Successful response from {endpoint}", extra=extra)
    
    def log_error(self, endpoint: str, error: Exception, error_code: str):
        self.logger.error(f"Error in {endpoint}: {error}", extra={
            "endpoint": endpoint,
            "error_code": error_code,
            "error_type": type(error).__name__
        })
    
    def log_validation_error(self, endpoint: str, errors: List[Any]):
        self.logger.warning(f"Validation failed in {endpoint}", extra={
            "endpoint": endpoint,
            "validation_errors": len(errors)
        })

logger = CentralizedLogger(__name__)

def standardized_endpoint(endpoint_name: str = None, requires_db: bool = True):
    # Decorator for logging and database dependency injection
    
    def decorator(func: Callable) -> Callable:
        name = endpoint_name or func.__name__
        central_logger = CentralizedLogger("api.endpoints")
        
        if requires_db:
            @wraps(func)
            async def standardized_func(*args, db: DatabaseManager = Depends(get_database), **kwargs):
                central_logger.log_request(name, kwargs)
                result = await func(*args, db, **kwargs)
                
                data_count = None
                if hasattr(result, 'data') and hasattr(result.data, '__len__'):
                    data_count = len(result.data)
                central_logger.log_success(name, data_count)
                
                return result
            return standardized_func
        else:
            @wraps(func)
            async def standardized_func_no_db(*args, **kwargs):
                central_logger.log_request(name, kwargs)
                result = await func(*args, **kwargs)
                
                data_count = None
                if hasattr(result, 'data') and hasattr(result.data, '__len__'):
                    data_count = len(result.data)
                central_logger.log_success(name, data_count)
                
                return result
            return standardized_func_no_db
    
    return decorator

class ValidationMixin:
    # Centralized validation processing for all validation types
    
    def __init__(self):
        self.validation_logger = CentralizedLogger("api.validation")
    
    async def validate_with_service(self, validator_class, config: Any, db: DatabaseManager) -> ValidationResult:
        # Generic validation service caller
        try:
            validator = validator_class(db)
            if hasattr(validator, 'validate_simulation_config'):
                return await validator.validate_simulation_config(config)
            elif hasattr(validator, 'validate'):
                return await validator.validate(config)
            else:
                raise ValueError(f"Validator {validator_class} has no known validation method")
        except Exception as e:
            self.validation_logger.log_error("validation_service", e, "VALIDATION_SYSTEM_ERROR")
            # Provide more specific error context for debugging
            error_context = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "validator_class": validator_class.__name__ if validator_class else "unknown"
            }
            raise HTTPException(
                status_code=500, 
                detail=f"Validation system error: {str(e)}",
                headers={"X-Error-Context": str(error_context)}
            )
    
    def process_validation_result(self, validation_result: ValidationResult, 
                                success_message: str = "Validation successful",
                                endpoint_name: str = "unknown") -> StandardResponse:
        # Standardized validation result processing with logging
        if not validation_result.is_valid:
            self.validation_logger.log_validation_error(endpoint_name, validation_result.errors)
            return create_error_response(
                "Validation failed",
                [ApiError(code="VALIDATION_FAILED", message=error.message, field=error.field) 
                 for error in validation_result.errors]
            )
        
        if validation_result.warnings:
            from response_models import create_warning_response
            return create_warning_response(
                validation_result,
                success_message + " (with warnings)",
                validation_result.warnings
            )
        
        return create_success_response(validation_result, success_message)

class BaseRouter(ABC, ValidationMixin):
    # Base router class focusing on core functionality
    
    def __init__(self):
        super().__init__()
        self.db_dependency = Depends(get_database)
        self.central_logger = CentralizedLogger(self.__class__.__name__)
    
    def handle_validation_result(self, validation_result: ValidationResult, success_message: str = "Validation successful") -> StandardResponse:
        # Delegate to the ValidationMixin method with endpoint context
        return self.process_validation_result(validation_result, success_message, self.__class__.__name__)
    
    def create_not_found_response(self, resource_name: str, identifier: str, field_name: str = "id") -> StandardResponse[None]:
        # Standardized not found response creation
        return create_error_response(
            f"{resource_name} not found",
            [ApiError(
                code=f"{resource_name.upper().replace(' ', '_')}_NOT_FOUND",
                message=f"{resource_name} not found",
                field=field_name
            )]
        )
    
    def create_success_with_metadata(self, data: Any, message: str, **metadata_kwargs) -> StandardResponse:
        # Standardized success response with metadata
        metadata = {}
        if hasattr(data, '__len__') and not isinstance(data, (str, dict)):
            metadata["count"] = len(data)
        metadata.update(metadata_kwargs)
        return create_success_response(data, message, metadata=metadata)

class DatabaseMixin:
    # Mixin providing standardized database operation patterns
    
    async def safe_db_operation(self, 
                              operation: Callable,
                              success_message: str,
                              error_message: str,
                              error_code: str,
                              *args, 
                              **kwargs) -> StandardResponse:
        # Execute database operations with standardized error handling
        try:
            result = await operation(*args, **kwargs)
            if result is None:
                return create_error_response(
                    "No data found",
                    [ApiError(code="NO_DATA_FOUND", message="No data found for the given parameters")]
                )
            return create_success_response(result, success_message)
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            return create_error_response(
                error_message,
                [ApiError(code=error_code, message=str(e))]
            )

# Custom exception classes for global handler
class ValidationError(Exception):
    def __init__(self, message: str, errors: List[ApiError] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)

class OperationError(Exception):
    def __init__(self, message: str, code: str = "OPERATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)