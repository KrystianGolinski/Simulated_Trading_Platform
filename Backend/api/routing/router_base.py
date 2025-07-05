# RouterBase - Minimal routing functionality with service injection
# Single responsibility: Core routing setup and service dependency injection

from typing import Optional
from fastapi import APIRouter
import logging

from api_components.validation_service import ValidationService
from api_components.response_formatter import ResponseFormatter
from api_components.router_logger import RouterLogger, EndpointLogger

logger = logging.getLogger(__name__)

class RouterBase:
    # Minimal router base with service injection
    # Single responsibility: Core routing setup and service coordination
    
    def __init__(self, router_name: str = "unnamed", 
                 validation_service: Optional[ValidationService] = None,
                 response_formatter: Optional[ResponseFormatter] = None,
                 router_logger: Optional[RouterLogger] = None):
        # Core router setup
        self.router = APIRouter()
        self.router_name = router_name
        
        # Service injection with defaults
        self.validation_service = validation_service or ValidationService()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.router_logger = router_logger or EndpointLogger.create_router_logger(router_name)
        
        # Log router creation
        logger.info(f"RouterBase created for {router_name}")
    
    def get_router(self) -> APIRouter:
        # Return the FastAPI router instance
        return self.router
    
    def log_router_startup(self):
        # Log router startup information
        self.router_logger.log_info(f"Router {self.router_name} initialized with injected services")
    
    def get_service_info(self) -> dict:
        # Return information about injected services for debugging
        return {
            "router_name": self.router_name,
            "validation_service": type(self.validation_service).__name__,
            "response_formatter": type(self.response_formatter).__name__,
            "router_logger": type(self.router_logger).__name__
        }