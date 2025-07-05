# Routing package - RouterBase and service injection
# Provides router architecture with dependency injection

from .router_base import RouterBase
from .service_factory import RouterServiceFactory, get_router_service_factory

__all__ = ['RouterBase', 'RouterServiceFactory', 'get_router_service_factory']