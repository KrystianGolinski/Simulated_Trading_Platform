# Routing Package - Advanced Router Architecture with Service Injection
# This package provides comprehensive router architecture with dependency injection for the Trading Platform API
# 
# Architecture Overview:
# The routing package implements a sophisticated router architecture that goes beyond basic FastAPI routing.
# It provides a foundation for building routers with consistent service injection, standardized logging,
# and unified validation patterns. This architecture ensures that all routers across the API maintain
# consistent behavior and can be easily extended or modified.
#
# Key Components:
# 1. RouterBase - Abstract base class providing core router functionality with service injection
# 2. RouterServiceFactory - Factory pattern implementation for creating and managing router services
# 3. Service injection pattern - Ensures consistent service availability across all routers
#
# Integration with Trading Platform:
# - Provides standardized foundation for all API endpoint routers
# - Integrates with api_components for validation, logging, and response formatting
# - Supports both singleton and per-router service instances as appropriate
# - Enables consistent error handling and logging across all endpoints
#
# Usage Pattern:
# Routers should extend RouterBase and utilize RouterServiceFactory for service creation.
# This ensures consistent behavior and simplifies testing through dependency injection.

from .router_base import RouterBase
from .service_factory import RouterServiceFactory, get_router_service_factory

__all__ = ['RouterBase', 'RouterServiceFactory', 'get_router_service_factory']