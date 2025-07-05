from typing import Dict, Any, Optional
import logging

from functools import wraps
from fastapi import Depends

logger = logging.getLogger(__name__)

class RouterLogger:
    # Centralized logging system for API operations
    # Single responsibility: Request/response logging and tracking
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_request(self, endpoint: str, params: Dict[str, Any] = None):
        # Log incoming request with parameters
        self.logger.info(f"Request to {endpoint}", extra={"params": params})
    
    def log_success(self, endpoint: str, data_count: Optional[int] = None):
        # Log successful response
        extra = {"endpoint": endpoint}
        if data_count is not None:
            extra["data_count"] = data_count
        self.logger.info(f"Successful response from {endpoint}", extra=extra)
    
    def log_error(self, endpoint: str, error: Exception, error_code: str):
        # Log error response
        self.logger.error(f"Error in {endpoint}: {error}", extra={
            "endpoint": endpoint,
            "error_code": error_code,
            "error_type": type(error).__name__
        })
    
    def log_validation_error(self, endpoint: str, errors: list):
        # Log validation error
        self.logger.warning(f"Validation failed in {endpoint}", extra={
            "endpoint": endpoint,
            "validation_errors": len(errors)
        })
    
    def log_database_operation(self, operation: str, table: str, params: Dict[str, Any] = None):
        # Log database operation
        self.logger.debug(f"Database operation: {operation} on {table}", extra={
            "operation": operation,
            "table": table,
            "params": params
        })
    
    def log_cache_operation(self, operation: str, cache_key: str, hit: bool = None):
        # Log cache operation
        extra = {"operation": operation, "cache_key": cache_key}
        if hit is not None:
            extra["cache_hit"] = hit
        self.logger.debug(f"Cache operation: {operation} for key {cache_key}", extra=extra)
    
    def log_performance_metric(self, endpoint: str, duration_ms: float, 
                             operation_type: str = "request"):
        # Log performance metrics
        self.logger.info(f"Performance metric: {endpoint} took {duration_ms}ms", extra={
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "operation_type": operation_type
        })
    
    def log_business_event(self, event_type: str, details: Dict[str, Any]):
        # Log business logic events
        self.logger.info(f"Business event: {event_type}", extra={
            "event_type": event_type,
            "details": details
        })

class EndpointLogger:
    # Factory for creating endpoint-specific loggers
    
    @staticmethod
    def create_logger(endpoint_name: str) -> RouterLogger:
        # Create logger for specific endpoint
        return RouterLogger(f"api.endpoints.{endpoint_name}")
    
    @staticmethod
    def create_router_logger(router_name: str) -> RouterLogger:
        # Create logger for specific router
        return RouterLogger(f"api.routers.{router_name}")

def standardized_endpoint_decorator(endpoint_name: str = None):
    # Decorator for logging endpoint operations

    def decorator(func):
        name = endpoint_name or func.__name__
        endpoint_logger = EndpointLogger.create_logger(name)
        
        @wraps(func)
        async def standardized_func(*args, **kwargs):
            endpoint_logger.log_request(name, kwargs)
            result = await func(*args, **kwargs)
            
            # Log success with data count (if available)
            data_count = None
            if hasattr(result, 'data') and hasattr(result.data, '__len__'):
                data_count = len(result.data)
            endpoint_logger.log_success(name, data_count)
            
            return result
        return standardized_func
    
    return decorator