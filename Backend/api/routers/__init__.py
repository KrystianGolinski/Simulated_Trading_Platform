# Routers Package - API Endpoint Organization and Route Management
# This package provides organized API endpoint modules for the Trading Platform API
# Following FastAPI router pattern for modular endpoint organization and clean architecture
#
# Package Contents:
# - health.py: System health monitoring and status endpoints
# - engine.py: C++ trading engine integration and testing endpoints
# - simulation.py: Simulation lifecycle management endpoints
# - stocks.py: Stock data and temporal validation endpoints
# - strategies.py: Trading strategy management endpoints
# - performance.py: Performance analytics and optimization endpoints
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure across all routers
# - Dependency injection integration for service and repository access
# - Standardized response formatting using ResponseFormatter
# - Comprehensive logging with RouterLogger for request/response tracking
# - Error handling with structured ApiError responses
# - Authentication and authorization support through dependency injection
# - Health monitoring endpoints for Kubernetes deployment
# - Performance optimization endpoints for system monitoring
#
# Router Organization:
# - Each router focuses on a specific domain (health, simulation, stocks, etc.)
# - Consistent endpoint naming conventions and HTTP method usage
# - Tag-based organization for API documentation grouping
# - Dependency injection for clean separation of concerns
# - Integration with routing/ infrastructure for service factory pattern
#
# Integration Points:
# - Uses routing/ layer for RouterBase pattern implementation
# - Integrates with services/ layer for business logic operations
# - Connects to repositories/ layer for data access operations
# - Utilizes api_components/ for response formatting and logging
# - Supports dependencies/ layer for service injection
