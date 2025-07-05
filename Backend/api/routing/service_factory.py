# Service Factory - Creates and configures router services
# Single responsibility: Service instantiation and configuration for routers

from typing import Dict, Any, Optional
import logging

from api_components.validation_service import ValidationService
from api_components.response_formatter import ResponseFormatter
from api_components.router_logger import RouterLogger, EndpointLogger
from routing.router_base import RouterBase

logger = logging.getLogger(__name__)

class RouterServiceFactory:
    # Factory for creating router services with consistent configuration
    # Enables service injection and configuration management
    
    def __init__(self):
        self._validation_service = None
        self._response_formatter = None
        self._router_loggers = {}
        
    def get_validation_service(self) -> ValidationService:
        # Singleton validation service
        if self._validation_service is None:
            self._validation_service = ValidationService()
            logger.debug("Created singleton ValidationService")
        return self._validation_service
    
    def get_response_formatter(self) -> ResponseFormatter:
        # Singleton response formatter
        if self._response_formatter is None:
            self._response_formatter = ResponseFormatter()
            logger.debug("Created singleton ResponseFormatter")
        return self._response_formatter
    
    def get_router_logger(self, router_name: str) -> RouterLogger:
        # Per-router logger instances
        if router_name not in self._router_loggers:
            self._router_loggers[router_name] = EndpointLogger.create_router_logger(router_name)
            logger.debug(f"Created RouterLogger for {router_name}")
        return self._router_loggers[router_name]
    
    def create_router_base(self, router_name: str, 
                          custom_services: Optional[Dict[str, Any]] = None) -> RouterBase:
        # Create RouterBase with injected services
        # Allows for custom service overrides while maintaining defaults
        services = custom_services or {}
        
        validation_service = services.get('validation_service') or self.get_validation_service()
        response_formatter = services.get('response_formatter') or self.get_response_formatter()
        router_logger = services.get('router_logger') or self.get_router_logger(router_name)
        
        router_base = RouterBase(
            router_name=router_name,
            validation_service=validation_service,
            response_formatter=response_formatter,
            router_logger=router_logger
        )
        
        logger.info(f"Created RouterBase for {router_name} with injected services")
        return router_base
    
    def get_service_registry(self) -> Dict[str, Any]:
        # Return registry of created services for debugging/monitoring
        return {
            "validation_service": self._validation_service,
            "response_formatter": self._response_formatter,
            "router_loggers": list(self._router_loggers.keys())
        }

# Global factory instance for consistent service management
router_service_factory = RouterServiceFactory()

def get_router_service_factory() -> RouterServiceFactory:
    # Access point for the global router service factory
    return router_service_factory