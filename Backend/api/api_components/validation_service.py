from typing import Any, List, Type, Optional
from abc import ABC, abstractmethod
import logging
from fastapi import HTTPException

from models import ValidationResult
from models import ApiError

logger = logging.getLogger(__name__)

class ValidationService:
    # Centralized validation processing for all validation types
    # Single responsibility: Input validation coordination
    
    def __init__(self):
        self.logger = logging.getLogger("api.validation")
    
    async def validate_with_service(self, validator_instance: Any, config: Any) -> ValidationResult:
        # Generic validation service caller
        try:
            if hasattr(validator_instance, 'validate_simulation_config'):
                return await validator_instance.validate_simulation_config(config)
            elif hasattr(validator_instance, 'validate'):
                return await validator_instance.validate(config)
            else:
                raise ValueError(f"Validator {type(validator_instance)} has no known validation method")
        except Exception as e:
            self.logger.error(f"Validation system error: {e}", extra={
                "error_type": type(e).__name__,
                "validator_class": type(validator_instance).__name__ if validator_instance else "unknown"
            })
            # Provide more specific error context for debugging
            error_context = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "validator_class": type(validator_instance).__name__ if validator_instance else "unknown"
            }
            raise HTTPException(
                status_code=500, 
                detail=f"Validation system error: {str(e)}",
                headers={"X-Error-Context": str(error_context)}
            )
    
    def create_validation_errors(self, validation_result: ValidationResult, endpoint_name: str = "unknown") -> List[ApiError]:
        # Convert ValidationResult errors to API errors
        if not validation_result.is_valid:
            self.logger.warning(f"Validation failed in {endpoint_name}", extra={
                "endpoint": endpoint_name,
                "validation_errors": len(validation_result.errors)
            })
            return [ApiError(code="VALIDATION_FAILED", message=error.message, field=error.field) 
                    for error in validation_result.errors]
        return []
    
    def has_validation_warnings(self, validation_result: ValidationResult) -> bool:
        # Check if validation result has warnings
        return validation_result.warnings is not None and len(validation_result.warnings) > 0
    
    def get_validation_warnings(self, validation_result: ValidationResult) -> List[str]:
        # Extract warnings from validation result
        if self.has_validation_warnings(validation_result):
            return validation_result.warnings
        return []
    
    def is_validation_successful(self, validation_result: ValidationResult) -> bool:
        # Check if validation passed
        return validation_result.is_valid
    
    def log_validation_error(self, endpoint: str, errors: List[Any]):
        # Log validation errors
        self.logger.warning(f"Validation failed in {endpoint}", extra={
            "endpoint": endpoint,
            "validation_errors": len(errors)
        })