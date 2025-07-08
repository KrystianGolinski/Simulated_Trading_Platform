# RouterServiceFactory - Advanced Service Factory with Singleton Management
# This module provides sophisticated service creation and management for the Trading Platform API
# 
# Architecture Overview:
# The RouterServiceFactory implements a comprehensive factory pattern for creating and managing
# router services with intelligent lifecycle management. It provides both singleton and per-instance
# service creation patterns, ensuring optimal resource utilization and consistent service behavior.
#
# Key Responsibilities:
# 1. Service instantiation with intelligent lifecycle management
# 2. Singleton pattern implementation for shared services
# 3. Per-router service creation for isolated functionality
# 4. Service configuration and customization support
# 5. Service registry and monitoring capabilities
#
# Factory Pattern Implementation:
# The factory uses a hybrid approach combining singleton and per-instance patterns:
# - Validation services are singleton to ensure consistent validation behavior
# - Response formatters are singleton to maintain consistent API responses
# - Router loggers are per-instance to provide router-specific logging context
#
# Integration with Trading Platform:
# - Provides centralized service creation for all API routers
# - Ensures consistent service configuration across the platform
# - Supports dependency injection patterns for testing and flexibility
# - Integrates with the platform's logging and monitoring infrastructure

from typing import Dict, Any, Optional
import logging

from api_components.validation_service import ValidationService
from api_components.response_formatter import ResponseFormatter
from api_components.router_logger import RouterLogger, EndpointLogger
from routing.router_base import RouterBase

logger = logging.getLogger(__name__)

class RouterServiceFactory:
    """
    Advanced Service Factory with Singleton Management for Router Services
    
    This class implements a sophisticated factory pattern for creating and managing
    router services with intelligent lifecycle management. It provides both singleton
    and per-instance service creation patterns, ensuring optimal resource utilization
    and consistent service behavior across the Trading Platform API.
    
    The factory uses a hybrid approach to service creation:
    - Singleton services (ValidationService, ResponseFormatter) for consistency
    - Per-instance services (RouterLogger) for context-specific functionality
    
    Key Features:
    - Intelligent service lifecycle management with lazy initialization
    - Singleton pattern implementation for shared services
    - Per-router service creation for isolated functionality
    - Service configuration and customization support
    - Service registry and monitoring capabilities
    - Memory-efficient service reuse and management
    
    Architecture Integration:
    The factory integrates with the platform's service architecture by providing
    centralized service creation, consistent configuration, and dependency injection
    support. It ensures that all routers have access to properly configured services
    while maintaining optimal resource utilization.
    """
    
    def __init__(self):
        """
        Initialize the RouterServiceFactory with empty service containers.
        
        This constructor sets up the internal state for managing singleton and
        per-instance services. It uses lazy initialization to create services
        only when they are first requested, improving startup performance.
        
        The factory maintains separate containers for:
        - Singleton services (validation, response formatting)
        - Per-instance services (router loggers)
        """
        # Singleton service containers (lazy initialization)
        self._validation_service = None
        self._response_formatter = None
        
        # Per-instance service containers
        self._router_loggers = {}
        
    def get_validation_service(self) -> ValidationService:
        """
        Get or create the singleton ValidationService instance.
        
        This method implements the singleton pattern for validation services,
        ensuring that all routers use the same validation service instance.
        This provides consistency in validation behavior across the platform.
        
        Returns:
            ValidationService: The singleton validation service instance
            
        The singleton pattern is used here because validation rules should be
        consistent across all routers, and sharing a single instance reduces
        memory usage and ensures consistent behavior.
        """
        if self._validation_service is None:
            self._validation_service = ValidationService()
            logger.debug("Created singleton ValidationService")
        return self._validation_service
    
    def get_response_formatter(self) -> ResponseFormatter:
        """
        Get or create the singleton ResponseFormatter instance.
        
        This method implements the singleton pattern for response formatters,
        ensuring that all routers use the same response formatting service.
        This provides consistency in API response structure across the platform.
        
        Returns:
            ResponseFormatter: The singleton response formatter instance
            
        The singleton pattern is used here because response formatting should be
        consistent across all endpoints, and sharing a single instance reduces
        memory usage and ensures consistent API behavior.
        """
        if self._response_formatter is None:
            self._response_formatter = ResponseFormatter()
            logger.debug("Created singleton ResponseFormatter")
        return self._response_formatter
    
    def get_router_logger(self, router_name: str) -> RouterLogger:
        """
        Get or create a router-specific logger instance.
        
        This method creates per-router logger instances to provide context-specific
        logging for each router. Each router gets its own logger instance to
        ensure proper logging context and isolation.
        
        Args:
            router_name: The name of the router (used for logging context)
            
        Returns:
            RouterLogger: A router-specific logger instance
            
        Per-instance loggers are used here because each router needs its own
        logging context to properly track and debug router-specific operations.
        """
        if router_name not in self._router_loggers:
            self._router_loggers[router_name] = EndpointLogger.create_router_logger(router_name)
            logger.debug(f"Created RouterLogger for {router_name}")
        return self._router_loggers[router_name]
    
    def create_router_base(self, router_name: str, 
                          custom_services: Optional[Dict[str, Any]] = None) -> RouterBase:
        """
        Create a fully configured RouterBase instance with service injection.
        
        This method is the primary factory method for creating RouterBase instances
        with properly injected services. It supports both default factory-managed
        services and custom service overrides for testing and specialized use cases.
        
        Args:
            router_name: Unique identifier for the router
            custom_services: Optional dictionary of custom service instances to inject
                           Keys: 'validation_service', 'response_formatter', 'router_logger'
                           
        Returns:
            RouterBase: A fully configured router instance with injected services
            
        The method implements a flexible service injection pattern:
        - Uses factory-managed services by default for consistency
        - Supports custom service injection for testing and specialized use cases
        - Maintains proper service lifecycle management
        - Provides comprehensive logging for debugging and monitoring
        """
        # Process custom service overrides or use factory defaults
        services = custom_services or {}
        
        # Service resolution with intelligent fallback to factory defaults
        validation_service = services.get('validation_service') or self.get_validation_service()
        response_formatter = services.get('response_formatter') or self.get_response_formatter()
        router_logger = services.get('router_logger') or self.get_router_logger(router_name)
        
        # Create RouterBase instance with injected services
        router_base = RouterBase(
            router_name=router_name,
            validation_service=validation_service,
            response_formatter=response_formatter,
            router_logger=router_logger
        )
        
        # Log router creation for debugging and monitoring
        logger.info(f"Created RouterBase for {router_name} with injected services")
        return router_base
    
    def get_service_registry(self) -> Dict[str, Any]:
        """
        Return comprehensive registry of created services for debugging and monitoring.
        
        This method provides detailed information about all services managed by the
        factory, including their current state and configuration. It's useful for
        debugging service injection issues and monitoring factory health.
        
        Returns:
            dict: Service registry containing:
                - validation_service: Current validation service instance (or None)
                - response_formatter: Current response formatter instance (or None)
                - router_loggers: List of router names that have loggers created
                
        The registry information is particularly useful for:
        - Debugging service injection issues
        - Monitoring factory resource usage
        - Understanding service lifecycle state
        - Testing service creation behavior
        """
        return {
            "validation_service": self._validation_service,
            "response_formatter": self._response_formatter,
            "router_loggers": list(self._router_loggers.keys())
        }

# Global singleton instance of the RouterServiceFactory.
# Ensures that all routers share the same service factory, providing consistent
# service creation and management throughout the platform.
router_service_factory = RouterServiceFactory()

def get_router_service_factory() -> RouterServiceFactory:
    """
    Get the global RouterServiceFactory instance.
    
    This function provides access to the application-wide router service factory,
    ensuring that all routers use the same factory instance for consistent service
    management. The global factory pattern ensures that singleton services are
    truly shared across the entire application.
    
    Returns:
        RouterServiceFactory: The global router service factory instance
        
    Usage:
        factory = get_router_service_factory()
        router_base = factory.create_router_base("my_router")
        
    The global factory pattern is used here to ensure that all routers share
    the same service instances where appropriate (singletons) while maintaining
    proper service isolation where needed (per-instance services).
    """
    return router_service_factory