# Health Router - System Health Monitoring and Status Endpoints
# This module provides comprehensive health monitoring endpoints for the Trading Platform API
# Key responsibilities:
# - System health monitoring and component status validation
# - Kubernetes-style readiness and liveness probes for container orchestration
# - Database connectivity validation through validation system integration
# - C++ trading engine health monitoring and accessibility checks
# - System resource monitoring (disk usage, memory usage)
# - Comprehensive health dashboard with detailed metrics and diagnostics
# - Service information and environment status reporting
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure and logging
# - Dependency injection integration for validation system access
# - Multi-component health aggregation with overall status determination
# - Kubernetes probe endpoint compatibility for container deployment
# - System resource monitoring with configurable thresholds
# - Comprehensive error handling and logging for health check failures
# - Health dashboard for monitoring and debugging purposes
#
# Endpoints Provided:
# - /: Root service information endpoint
# - /health: Comprehensive health check with all system components
# - /health/ready: Kubernetes readiness probe for traffic acceptance
# - /health/live: Kubernetes liveness probe for service availability
# - /health/dashboard: Detailed health dashboard with metrics and status
#
# Health Components Monitored:
# - Database connectivity and validation system status
# - C++ trading engine availability and accessibility
# - System resources (disk usage, memory usage)
# - Overall service health with degradation detection
#
# Integration Points:
# - Uses SimulationValidator for database connectivity validation
# - Integrates with engine health checking functions
# - Utilizes system resource monitoring for comprehensive health assessment
# - Supports RouterBase pattern for consistent response formatting

import os
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends

from dependencies import get_simulation_validator
from models import ApiError, StandardResponse
from routing import get_router_service_factory
from validation import SimulationValidator

# Create router using RouterBase pattern for consistent health endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("health")
router = router_base.get_router()
router.tags = ["health"]


async def check_cpp_engine_health() -> Dict[str, Any]:
    # Check C++ trading engine availability and accessibility across deployment scenarios
    # Validates engine binary existence and execution permissions
    # Returns structured health status for engine component monitoring
    try:
        # Check multiple engine binary locations for different deployment scenarios
        engine_paths = [
            Path("/shared/trading_engine"),  # Docker shared volume mount
            Path("/app/cpp-engine/build/trading_engine"),  # Container local build
            Path(__file__).parent.parent.parent
            / "cpp-engine"
            / "build"
            / "trading_engine",  # Development build
        ]

        # Iterate through possible engine locations to find valid executable
        for engine_path in engine_paths:
            if engine_path.exists() and os.access(engine_path, os.X_OK):
                return {
                    "status": "healthy",
                    "engine_path": str(engine_path),
                    "executable": True,
                }

        # Return unhealthy status if no valid engine found
        return {
            "status": "unhealthy",
            "engine_path": None,
            "executable": False,
            "error": "C++ engine binary not found or not executable",
        }
    except Exception as e:
        # Handle engine health check errors with structured error response
        return {"status": "unhealthy", "error": str(e)}


def get_system_health() -> Dict[str, Any]:
    # Get comprehensive system resource health metrics for monitoring
    # Monitors disk usage, memory usage, and system resource availability
    # Returns structured metrics for health threshold evaluation
    try:
        import shutil

        import psutil

        # Calculate disk usage metrics for storage monitoring
        disk_usage = shutil.disk_usage("/")
        disk_usage_pct = (disk_usage.used / disk_usage.total) * 100

        # Calculate memory usage metrics for resource monitoring
        memory = psutil.virtual_memory()

        # Return comprehensive system metrics for health assessment
        return {
            "disk_usage_pct": round(disk_usage_pct, 2),
            "available_disk_gb": round(disk_usage.free / (1024**3), 2),
            "total_disk_gb": round(disk_usage.total / (1024**3), 2),
            "memory_usage_pct": memory.percent,
            "available_memory_mb": round(memory.available / (1024**2), 2),
            "total_memory_gb": round(memory.total / (1024**3), 2),
        }
    except ImportError:
        # Fallback to basic disk monitoring when psutil not available
        try:
            import shutil

            disk_usage = shutil.disk_usage("/")
            disk_usage_pct = (disk_usage.used / disk_usage.total) * 100

            # Return limited metrics when advanced monitoring unavailable
            return {
                "disk_usage_pct": round(disk_usage_pct, 2),
                "available_disk_gb": round(disk_usage.free / (1024**3), 2),
                "total_disk_gb": round(disk_usage.total / (1024**3), 2),
                "memory_info": "psutil not available",
            }
        except Exception as e:
            # Handle basic system monitoring errors
            return {"error": f"System health check failed: {str(e)}"}
    except Exception as e:
        # Handle comprehensive system monitoring errors
        return {"error": f"System health check failed: {str(e)}"}


@router.get("/")
async def root() -> StandardResponse[Dict[str, str]]:
    # Root service information endpoint providing basic service identification
    # Returns service name, version, and running status for API discovery
    # Used for service verification and basic connectivity testing
    router_base.log_request("/")

    return router_base.success_response(
        "/",
        {"service": "Trading Platform API", "version": "1.0.0"},
        "Trading Platform API is running",
    )


@router.get("/health/ready")
async def readiness_check(
    validator: SimulationValidator = Depends(get_simulation_validator),
) -> StandardResponse[Dict[str, Any]]:
    # Kubernetes readiness probe - validates service readiness to accept traffic
    # Checks critical dependencies required for request processing
    # Returns ready/not-ready status for container orchestration systems
    try:
        # Validate database connectivity as critical readiness requirement
        validation_health = await validator.check_database_connection()

        # Evaluate readiness based on database connectivity status
        if validation_health.is_valid:
            return router_base.success_response(
                "/health/ready",
                {"ready": True, "database": "connected"},
                "Service ready to accept traffic",
            )
        else:
            return router_base.error_response(
                "/health/ready",
                "Service not ready",
                [ApiError(code="NOT_READY", message="Database connection failed")],
                Exception("Database connection failed"),
                "NOT_READY",
            )
    except Exception as e:
        # Handle readiness check errors for Kubernetes probe reliability
        return router_base.error_response(
            "/health/ready",
            "Readiness check failed",
            [ApiError(code="READINESS_ERROR", message=str(e))],
            e,
            "READINESS_ERROR",
        )


@router.get("/health/live")
async def liveness_check() -> StandardResponse[Dict[str, Any]]:
    # Kubernetes liveness probe - validates service process is alive and responsive
    # Simple endpoint that confirms API process is running and can handle requests
    # Used by container orchestration for restart decision making
    router_base.log_request("/health/live")

    return router_base.success_response(
        "/health/live", {"alive": True, "timestamp": time.time()}, "Service is alive"
    )


@router.get("/health")
async def health_check(
    validator: SimulationValidator = Depends(get_simulation_validator),
) -> StandardResponse[Dict[str, Any]]:
    # Comprehensive health check with all system components and dependencies
    # Aggregates health status from database, engine, validation system, and resources
    # Provides detailed diagnostic information for system monitoring and troubleshooting
    try:
        start_time = time.time()

        # Validate database connectivity through validation system integration
        validation_health = await validator.check_database_connection()

        # Create database health structure for health aggregation
        db_health = {
            "status": "healthy" if validation_health.is_valid else "unhealthy",
            "data_stats": {"symbols_daily": 0, "daily_records": 0},
            "error": (
                validation_health.errors[0].message
                if validation_health.errors
                else None
            ),
        }

        # Validate C++ trading engine availability and accessibility
        cpp_engine_health = await check_cpp_engine_health()

        # Monitor system resources for capacity and performance
        system_health = get_system_health()

        # Aggregate component health status to determine overall system health
        overall_status = "healthy"
        health_issues = []

        # Evaluate database health impact on overall status
        if db_health["status"] != "healthy":
            overall_status = "degraded"
            health_issues.append("Database connection issues")

        # Evaluate validation system health impact
        if not validation_health.is_valid:
            overall_status = "degraded"
            health_issues.append("Validation system errors")

        # Evaluate C++ engine health impact
        if cpp_engine_health["status"] != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"
            health_issues.append("C++ engine unavailable")

        # Evaluate system resource health with configurable thresholds
        if (
            system_health["disk_usage_pct"] > 90
            or system_health["available_memory_mb"] < 100
        ):
            if overall_status == "healthy":
                overall_status = "degraded"
            health_issues.append("System resources low")

        # Calculate health check response time for performance monitoring
        response_time = round((time.time() - start_time) * 1000, 2)

        # Compile comprehensive health data for monitoring and diagnostics
        health_data = {
            "service": "trading-api",
            "overall_status": overall_status,
            "response_time_ms": response_time,
            "timestamp": time.time(),
            "issues": health_issues,
            "stocks_count": db_health.get("data_stats", {}).get("symbols_daily", 0),
            "components": {
                "database": db_health,
                "validation_system": {
                    "status": "healthy" if validation_health.is_valid else "degraded",
                    "errors": [
                        error.model_dump() for error in validation_health.errors
                    ],
                    "warnings": validation_health.warnings,
                },
                "cpp_engine": cpp_engine_health,
                "system_resources": system_health,
            },
        }

        # Format health response based on overall system status
        if overall_status == "healthy":
            return router_base.success_response(
                "/health", health_data, "All systems healthy"
            )
        else:
            response = router_base.response_formatter.create_error_response(
                f"System health check failed: {', '.join(health_issues)}",
                [
                    ApiError(
                        code="HEALTH_CHECK_FAILED",
                        message=f"System status: {overall_status}",
                    )
                ],
            )
            router_base.router_logger.log_error(
                "/health",
                Exception(f"Health issues: {health_issues}"),
                "HEALTH_CHECK_FAILED",
            )
            return response
    except Exception as e:
        # Handle comprehensive health check errors with detailed logging
        router_base.router_logger.log_error("/health", e, "HEALTH_CHECK_ERROR")
        return router_base.response_formatter.create_error_response(
            "Health check failed", [ApiError(code="HEALTH_CHECK_ERROR", message=str(e))]
        )


@router.get("/health/dashboard")
async def health_dashboard(
    validator: SimulationValidator = Depends(get_simulation_validator),
) -> StandardResponse[Dict[str, Any]]:
    # Comprehensive health dashboard with service metrics, endpoints, and monitoring configuration
    # Provides detailed health overview for monitoring systems and debugging
    # Includes service information, health endpoints, and monitoring configuration
    try:
        # Compile dashboard data with service information and monitoring configuration
        dashboard_data = {
            "service_info": {
                "name": "Trading Platform API",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
            "health_endpoints": {
                "main_health": "/health",
                "readiness": "/health/ready",
                "liveness": "/health/live",
                "dashboard": "/health/dashboard",
            },
            "monitoring_info": {
                "health_check_interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s",
            },
        }

        # Include current health status in dashboard data
        health_result = await health_check(validator)
        if health_result.data:
            dashboard_data["current_health"] = health_result.data

        return router_base.success_response(
            "/health/dashboard",
            dashboard_data,
            "Health dashboard data retrieved successfully",
        )
    except Exception as e:
        # Handle dashboard generation errors with comprehensive error reporting
        return router_base.error_response(
            "/health/dashboard",
            "Failed to generate health dashboard",
            [ApiError(code="DASHBOARD_ERROR", message=str(e))],
            e,
            "DASHBOARD_ERROR",
        )
