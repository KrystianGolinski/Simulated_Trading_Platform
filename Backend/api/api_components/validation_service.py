# Validation Service - Centralized Input Validation Coordination
# This module provides comprehensive validation service coordination for the Trading Platform API
# Key responsibilities:
# - Generic validation service coordination and method dispatch
# - Validation result processing and standardization
# - Error handling and logging for validation operations
# - Warning extraction and processing from validation results
# - ValidationResult to ApiError transformation
# - Validation status checking and utility methods
# - HTTP exception handling for validation system errors
#
# Architecture Features:
# - Generic validator instance support with method discovery
# - Consistent error handling across all validation types
# - Structured logging with validation context
# - HTTP exception handling with detailed error context
# - Warning and error separation for different response types
# - Validation result utility methods for common operations

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

from fastapi import HTTPException

from models import ApiError, ValidationResult

logger = logging.getLogger(__name__)


class ValidationService:
    # Centralized validation service for coordinating different validation types
    # Provides generic validation method dispatch and result processing
    # Handles validation errors and HTTP exception conversion

    def __init__(self):
        # Initialize validation service with dedicated logger for validation operations
        self.logger = logging.getLogger("api.validation")

    async def validate_with_service(
        self, validator_instance: Any, config: Any
    ) -> ValidationResult:
        # Generic validation method dispatcher with automatic method discovery
        # Supports different validator interfaces through duck typing
        # Handles validation errors and converts them to HTTP exceptions
        try:
            if hasattr(validator_instance, "validate_simulation_config"):
                return await validator_instance.validate_simulation_config(config)
            elif hasattr(validator_instance, "validate"):
                return await validator_instance.validate(config)
            else:
                raise ValueError(
                    f"Validator {type(validator_instance)} has no known validation method"
                )
        except Exception as e:
            self.logger.error(
                f"Validation system error: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "validator_class": (
                        type(validator_instance).__name__
                        if validator_instance
                        else "unknown"
                    ),
                },
            )
            # Provide comprehensive error context for debugging and monitoring
            error_context = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "validator_class": (
                    type(validator_instance).__name__
                    if validator_instance
                    else "unknown"
                ),
            }
            raise HTTPException(
                status_code=500,
                detail=f"Validation system error: {str(e)}",
                headers={"X-Error-Context": str(error_context)},
            )

    def create_validation_errors(
        self, validation_result: ValidationResult, endpoint_name: str = "unknown"
    ) -> List[ApiError]:
        # Convert ValidationResult errors to standardized ApiError format
        # Logs validation failures for monitoring and debugging
        # Returns empty list for successful validations
        if not validation_result.is_valid:
            self.logger.warning(
                f"Validation failed in {endpoint_name}",
                extra={
                    "endpoint": endpoint_name,
                    "validation_errors": len(validation_result.errors),
                },
            )
            return [
                ApiError(
                    code="VALIDATION_FAILED", message=error.message, field=error.field
                )
                for error in validation_result.errors
            ]
        return []

    def has_validation_warnings(self, validation_result: ValidationResult) -> bool:
        # Check if validation result contains warnings that should be reported
        # Used to determine response type (success vs warning)
        return (
            validation_result.warnings is not None
            and len(validation_result.warnings) > 0
        )

    def get_validation_warnings(self, validation_result: ValidationResult) -> List[str]:
        # Extract warning messages from validation result for response inclusion
        # Returns empty list if no warnings present
        if self.has_validation_warnings(validation_result):
            return validation_result.warnings
        return []

    def is_validation_successful(self, validation_result: ValidationResult) -> bool:
        # Check if validation passed without errors
        # Used for flow control in endpoint handlers
        return validation_result.is_valid

    def log_validation_error(self, endpoint: str, errors: List[Any]):
        # Log validation errors for monitoring and debugging
        # Uses warning level as validation errors are typically client-side issues
        self.logger.warning(
            f"Validation failed in {endpoint}",
            extra={"endpoint": endpoint, "validation_errors": len(errors)},
        )
