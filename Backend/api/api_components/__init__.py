# API Components Package - Reusable API Layer Components
# This package provides modular, reusable components for the Trading Platform API
# Components follow the single responsibility principle for maintainability and testability
#
# Package Contents:
# - ValidationService: Centralized validation coordination and error handling
# - ResponseFormatter: Standardized API response creation and formatting
# - RouterLogger: Comprehensive request/response logging with performance metrics
# - EndpointLogger: Factory for creating endpoint-specific loggers
# - standardized_endpoint_decorator: Automatic endpoint logging decorator
#
# Architecture Principles:
# - Single responsibility principle for each component
# - Dependency injection support for testing
# - Consistent error handling and logging patterns
# - Type safety with proper generic support
# - Structured logging with contextual information

from .response_formatter import ResponseFormatter
from .router_logger import EndpointLogger, RouterLogger, standardized_endpoint_decorator
from .validation_service import ValidationService

__all__ = [
    "ValidationService",
    "ResponseFormatter",
    "RouterLogger",
    "EndpointLogger",
    "standardized_endpoint_decorator",
]
