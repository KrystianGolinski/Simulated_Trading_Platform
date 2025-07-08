# Router Logger - Centralized API Request and Response Logging System
# This module provides comprehensive logging capabilities for API operations
# Key responsibilities:
# - Standardized request and response logging across all endpoints
# - Performance metrics tracking and monitoring
# - Error logging with detailed context and categorization
# - Business event logging for domain-specific operations
# - Database operation logging with parameter tracking
# - Cache operation logging with hit/miss tracking
# - Validation error logging with detailed error context
# - Endpoint-specific logger creation and management
#
# Architecture Features:
# - Factory pattern for creating endpoint-specific loggers
# - Decorator pattern for automatic endpoint logging
# - Structured logging with extra context for monitoring
# - Performance metrics integration
# - Business logic event tracking
# - Consistent log formatting across all operations

from typing import Dict, Any, Optional
import logging

from functools import wraps
from fastapi import Depends

logger = logging.getLogger(__name__)

class RouterLogger:
    # Centralized logging system for API operations with structured logging support
    # Provides comprehensive logging capabilities for request/response cycles
    # Integrates performance metrics, error tracking, and business event logging
    
    def __init__(self, name: str):
        # Initialize router logger with hierarchical logger name for organized log management
        self.logger = logging.getLogger(name)
    
    def log_request(self, endpoint: str, params: Dict[str, Any] = None):
        # Log incoming API request with parameters for monitoring and debugging
        # Includes request parameters for context and troubleshooting
        self.logger.info(f"Request to {endpoint}", extra={"params": params})
    
    def log_success(self, endpoint: str, data_count: Optional[int] = None):
        # Log successful API response with optional data count for monitoring
        # Includes data count for payload size tracking and performance analysis
        extra = {"endpoint": endpoint}
        if data_count is not None:
            extra["data_count"] = data_count
        self.logger.info(f"Successful response from {endpoint}", extra=extra)
    
    def log_error(self, endpoint: str, error: Exception, error_code: str):
        # Log error response with detailed context for debugging and monitoring
        # Includes error type and code for categorization and alerting
        self.logger.error(f"Error in {endpoint}: {error}", extra={
            "endpoint": endpoint,
            "error_code": error_code,
            "error_type": type(error).__name__
        })
    
    def log_validation_error(self, endpoint: str, errors: list):
        # Log validation error with error count for monitoring validation issues
        # Uses warning level as validation errors are typically client-side issues
        self.logger.warning(f"Validation failed in {endpoint}", extra={
            "endpoint": endpoint,
            "validation_errors": len(errors)
        })
    
    def log_database_operation(self, operation: str, table: str, params: Dict[str, Any] = None):
        # Log database operation with operation type, table, and parameters
        # Uses debug level for detailed database operation tracking
        self.logger.debug(f"Database operation: {operation} on {table}", extra={
            "operation": operation,
            "table": table,
            "params": params
        })
    
    def log_cache_operation(self, operation: str, cache_key: str, hit: bool = None):
        # Log cache operation with hit/miss tracking for performance monitoring
        # Tracks cache efficiency and identifies potential cache optimization opportunities
        extra = {"operation": operation, "cache_key": cache_key}
        if hit is not None:
            extra["cache_hit"] = hit
        self.logger.debug(f"Cache operation: {operation} for key {cache_key}", extra=extra)
    
    def log_performance_metric(self, endpoint: str, duration_ms: float, 
                             operation_type: str = "request"):
        # Log performance metrics for monitoring and optimization
        # Tracks execution time for performance analysis and bottleneck identification
        self.logger.info(f"Performance metric: {endpoint} took {duration_ms}ms", extra={
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "operation_type": operation_type
        })
    
    def log_business_event(self, event_type: str, details: Dict[str, Any]):
        # Log business logic events for domain-specific monitoring
        # Tracks important business operations and state changes
        self.logger.info(f"Business event: {event_type}", extra={
            "event_type": event_type,
            "details": details
        })

class EndpointLogger:
    # Factory class for creating endpoint-specific loggers with hierarchical naming
    # Provides consistent logger naming conventions across the API
    
    @staticmethod
    def create_logger(endpoint_name: str) -> RouterLogger:
        # Create logger for specific endpoint with hierarchical naming
        # Enables log filtering and organization by endpoint
        return RouterLogger(f"api.endpoints.{endpoint_name}")
    
    @staticmethod
    def create_router_logger(router_name: str) -> RouterLogger:
        # Create logger for specific router with hierarchical naming
        # Enables log filtering and organization by router module
        return RouterLogger(f"api.routers.{router_name}")

def standardized_endpoint_decorator(endpoint_name: str = None):
    # Decorator for automatic endpoint logging with request/response tracking
    # Provides consistent logging across all decorated endpoints
    # Automatically extracts data count from responses for monitoring

    def decorator(func):
        name = endpoint_name or func.__name__
        endpoint_logger = EndpointLogger.create_logger(name)
        
        @wraps(func)
        async def standardized_func(*args, **kwargs):
            # Log incoming request with parameters
            endpoint_logger.log_request(name, kwargs)
            result = await func(*args, **kwargs)
            
            # Extract data count from response for monitoring
            data_count = None
            if hasattr(result, 'data') and hasattr(result.data, '__len__'):
                data_count = len(result.data)
            endpoint_logger.log_success(name, data_count)
            
            return result
        return standardized_func
    
    return decorator