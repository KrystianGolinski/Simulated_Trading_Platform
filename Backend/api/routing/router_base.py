# RouterBase - Advanced Router Foundation with Service Injection
# This module provides the core router foundation for the Trading Platform API
#
# Architecture Overview:
# RouterBase implements a sophisticated base class for all API routers, providing standardized
# service injection, logging, and validation patterns. It serves as the foundation for building
# consistent, testable, and maintainable API endpoints across the trading platform.
#
# Key Responsibilities:
# 1. Core FastAPI router setup and configuration
# 2. Service dependency injection with intelligent defaults
# 3. Standardized logging integration for all router operations
# 4. Validation service coordination for consistent input validation
# 5. Response formatting service integration for standardized API responses
#
# Service Injection Pattern:
# RouterBase uses constructor injection to provide services to routers, allowing for:
# - Easy testing through mock service injection
# - Consistent service behavior across all routers
# - Flexible service configuration and overrides
# - Singleton pattern support for shared services
#
# Integration with Trading Platform:
# - Provides base functionality for all endpoint routers (stocks, simulation, strategies, etc.)
# - Integrates with api_components for validation, logging, and response formatting
# - Supports the platform's architectural patterns for dependency injection
# - Enables consistent error handling and logging across all endpoints

import logging
from typing import Optional

from fastapi import APIRouter

from api_components.response_formatter import ResponseFormatter
from api_components.router_logger import EndpointLogger, RouterLogger
from api_components.validation_service import ValidationService

logger = logging.getLogger(__name__)


class RouterBase:
    """
    Advanced Router Foundation with Service Injection

    This class provides the core foundation for all API routers in the Trading Platform,
    implementing standardized service injection, logging, and validation patterns.

    The RouterBase class serves as the foundation for building consistent, testable, and
    maintainable API endpoints. It provides dependency injection for core services,
    standardized logging integration, and consistent router configuration.

    Key Features:
    - Constructor-based service injection with intelligent defaults
    - Integrated logging with router-specific context
    - Validation service coordination for consistent input validation
    - Response formatting service integration for standardized API responses
    - Service information exposure for debugging and monitoring

    Architecture Integration:
    RouterBase integrates with the platform's service architecture by providing
    standardized access to validation services, response formatters, and logging
    capabilities. This ensures consistent behavior across all API endpoints.
    """

    def __init__(
        self,
        router_name: str = "unnamed",
        validation_service: Optional[ValidationService] = None,
        response_formatter: Optional[ResponseFormatter] = None,
        router_logger: Optional[RouterLogger] = None,
    ):
        """
        Initialize RouterBase with service injection and router configuration.

        This constructor sets up the core FastAPI router and injects required services
        with intelligent defaults. It provides a standardized foundation for all API
        routers in the trading platform.

        Args:
            router_name: Unique identifier for the router (used for logging and debugging)
            validation_service: Optional validation service instance (defaults to new ValidationService)
            response_formatter: Optional response formatter instance (defaults to new ResponseFormatter)
            router_logger: Optional router logger instance (defaults to router-specific logger)

        The constructor implements the dependency injection pattern, allowing services
        to be injected for testing while providing sensible defaults for production use.
        """
        # Core router setup with FastAPI integration
        self.router = APIRouter()
        self.router_name = router_name

        # Service injection with intelligent defaults
        # Each service can be injected for testing or use platform defaults
        self.validation_service = validation_service or ValidationService()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.router_logger = router_logger or EndpointLogger.create_router_logger(
            router_name
        )

        # Log router creation for debugging and monitoring
        logger.info(f"RouterBase created for {router_name} with injected services")

    def get_router(self) -> APIRouter:
        """
        Return the FastAPI router instance for integration with the main application.

        This method provides access to the underlying FastAPI router that contains
        all the configured endpoints. It's used by the main application to register
        the router with the FastAPI app instance.

        Returns:
            APIRouter: The configured FastAPI router instance
        """
        return self.router

    def log_router_startup(self):
        """
        Log router startup information for debugging and monitoring.

        This method logs important information about the router's initialization,
        including service injection status and configuration details. It should be
        called after the router is fully configured and ready to handle requests.

        The startup logging provides visibility into the router's configuration
        and helps with debugging service injection issues.
        """
        self.router_logger.log_info(
            f"Router {self.router_name} initialized with injected services"
        )

    def get_service_info(self) -> dict:
        """
        Return detailed information about injected services for debugging and monitoring.

        This method provides comprehensive information about the services that have
        been injected into the router, including their types and configuration.
        It's useful for debugging service injection issues and monitoring router health.

        Returns:
            dict: Service information containing:
                - router_name: The name of the router
                - validation_service: Type name of the validation service
                - response_formatter: Type name of the response formatter
                - router_logger: Type name of the router logger

        The service information is particularly useful for testing and debugging
        to ensure that the correct services have been injected.
        """
        return {
            "router_name": self.router_name,
            "validation_service": type(self.validation_service).__name__,
            "response_formatter": type(self.response_formatter).__name__,
            "router_logger": type(self.router_logger).__name__,
        }

    def success_response(
        self, endpoint: str, data, message: str = "Success", data_count=None
    ):
        """Create success response with automatic logging and return."""
        response = self.response_formatter.create_success_response(data, message)
        self.router_logger.log_success(endpoint, data_count)
        return response

    def error_response(
        self,
        endpoint: str,
        message: str,
        errors=None,
        exception=None,
        error_code: str = "ERROR",
    ):
        """Create error response with automatic logging and return."""
        response = self.response_formatter.create_error_response(message, errors or [])
        if exception:
            self.router_logger.log_error(endpoint, exception, error_code)
        return response

    def log_request(self, endpoint: str, params=None):
        """Log request with optional parameters."""
        self.router_logger.log_request(endpoint, params or {})
