# Response Formatter - Standardized API Response Creation Service
# This module provides comprehensive response formatting capabilities for the Trading Platform API
# Key responsibilities:
# - Standardized response structure creation with proper typing
# - Validation result processing and error formatting
# - Success, warning, and error response generation
# - Database operation result formatting with proper error handling
# - Paginated response structure creation
# - Metadata enrichment for responses
# - Consistent error code and message formatting
# - Resource not found response standardization
#
# Architecture Features:
# - Single responsibility principle for response formatting
# - Consistent error handling and logging integration
# - Type-safe response creation using StandardResponse models
# - Metadata support for enhanced API responses
# - Paginated response support for large datasets
# - Validation result integration with proper error categorization

import logging
from typing import Any, Dict, List, Optional

from models import (
    ApiError,
    PaginatedResponse,
    StandardResponse,
    ValidationResult,
    create_error_response,
    create_paginated_response,
    create_success_response,
    create_warning_response,
)

logger = logging.getLogger(__name__)


class ResponseFormatter:
    # Centralized response formatting service for consistent API responses
    # Provides standardized response creation with proper error handling and logging
    # Ensures consistent response structure across all API endpoints

    def __init__(self):
        # Initialize response formatter with dedicated logger for response operations
        self.logger = logging.getLogger("api.response_formatter")

    def format_validation_response(
        self,
        validation_result: ValidationResult,
        success_message: str = "Validation successful",
        endpoint_name: str = "unknown",
    ) -> StandardResponse:
        # Process validation result and format appropriate response based on validation state
        # Handles three validation states: error, warning, and success
        # Returns properly formatted StandardResponse with appropriate status and messaging
        if not validation_result.is_valid:
            return self.create_validation_error_response(
                validation_result, endpoint_name
            )

        if validation_result.warnings:
            return self.create_validation_warning_response(
                validation_result, success_message
            )

        return create_success_response(validation_result, success_message)

    def create_validation_error_response(
        self, validation_result: ValidationResult, endpoint_name: str = "unknown"
    ) -> StandardResponse:
        # Create standardized validation error response with structured error details
        # Logs validation failure with context for monitoring and debugging
        # Transforms validation errors into standardized ApiError format
        self.logger.warning(
            f"Validation failed in {endpoint_name}",
            extra={
                "endpoint": endpoint_name,
                "validation_errors": len(validation_result.errors),
            },
        )

        return create_error_response(
            "Validation failed",
            [
                ApiError(
                    code="VALIDATION_FAILED", message=error.message, field=error.field
                )
                for error in validation_result.errors
            ],
        )

    def create_validation_warning_response(
        self, validation_result: ValidationResult, success_message: str
    ) -> StandardResponse:
        # Create standardized validation warning response for successful validation with warnings
        # Indicates validation passed but with non-critical issues that should be addressed
        # Appends warning indication to success message for clarity
        return create_warning_response(
            validation_result,
            success_message + " (with warnings)",
            validation_result.warnings,
        )

    def create_not_found_response(
        self, resource_name: str, identifier: str, field_name: str = "id"
    ) -> StandardResponse[None]:
        # Create standardized 'not found' response for resource lookup failures
        # Automatically generates appropriate error codes based on resource name
        # Provides consistent error format for all resource types
        return create_error_response(
            f"{resource_name} not found",
            [
                ApiError(
                    code=f"{resource_name.upper().replace(' ', '_')}_NOT_FOUND",
                    message=f"{resource_name} not found",
                    field=field_name,
                )
            ],
        )

    def create_success_with_metadata(
        self, data: Any, message: str, **metadata_kwargs
    ) -> StandardResponse:
        # Create standardized success response with enriched metadata
        # Automatically adds count metadata for collections
        # Allows custom metadata addition through kwargs
        metadata = {}
        if hasattr(data, "__len__") and not isinstance(data, (str, dict)):
            metadata["count"] = len(data)
        metadata.update(metadata_kwargs)
        return create_success_response(data, message, metadata=metadata)

    def create_database_error_response(
        self, error_message: str, error_code: str, exception: Exception
    ) -> StandardResponse:
        # Create standardized database error response with proper logging
        # Logs database errors for monitoring and debugging
        # Transforms exceptions into standardized ApiError format
        self.logger.error(f"Database operation failed: {error_message} - {exception}")
        return create_error_response(
            error_message, [ApiError(code=error_code, message=str(exception))]
        )

    def create_no_data_response(
        self, message: str = "No data found"
    ) -> StandardResponse:
        # Create standardized response for empty result sets
        # Provides consistent handling of no-data scenarios
        # Uses standard NO_DATA_FOUND error code for client handling
        return create_error_response(
            message,
            [
                ApiError(
                    code="NO_DATA_FOUND",
                    message="No data found for the given parameters",
                )
            ],
        )

    def format_paginated_response(
        self,
        data: List[Any],
        total_count: int,
        page: int,
        page_size: int,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> PaginatedResponse:
        # Create standardized paginated response with navigation metadata
        # Includes pagination information for client navigation
        # Supports custom metadata for enhanced pagination features
        return create_paginated_response(
            data=data,
            page=page,
            page_size=page_size,
            total_count=total_count,
            message=message,
            metadata=metadata,
        )

    def format_operation_result(
        self, result: Any, success_message: str, error_message: str, error_code: str
    ) -> StandardResponse:
        # Format database operation result with proper error handling
        # Handles three scenarios: no data, successful operation, and operation failure
        # Provides consistent error handling for database operations
        if result is None:
            return self.create_no_data_response()

        try:
            return create_success_response(result, success_message)
        except Exception as e:
            return self.create_database_error_response(error_message, error_code, e)

    def create_success_response(
        self, data: Any, message: str = "Success", metadata: Optional[Dict] = None
    ) -> StandardResponse:
        # Create standardized success response with optional metadata
        # Provides default success message while allowing customization
        # Supports metadata enhancement for additional response context
        return create_success_response(data, message, metadata=metadata)

    def create_error_response(
        self, message: str, errors: List[ApiError] = None
    ) -> StandardResponse:
        # Create standardized error response with optional detailed errors
        # Provides consistent error formatting across all endpoints
        # Supports both simple error messages and detailed error lists
        return create_error_response(message, errors)
