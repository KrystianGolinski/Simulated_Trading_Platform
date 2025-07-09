# Performance Router - Performance Analytics and Optimization Monitoring Endpoints
# This module provides API endpoints for performance monitoring and optimization analytics
# Key responsibilities:
# - Performance statistics retrieval and monitoring
# - Cache performance analytics and hit/miss ratios
# - Performance cache management and clearing operations
# - Optimization metrics tracking and analysis
# - System performance monitoring for parallel execution
# - Memory usage statistics and optimization insights
# - Performance bottleneck identification and reporting
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure and logging
# - Integration with PerformanceOptimizer for comprehensive metrics
# - Real-time performance statistics with timestamp tracking
# - Cache management operations for performance tuning
# - Error handling for performance monitoring failures
# - Structured response formatting for analytics data
# - Performance metrics aggregation and reporting
#
# Endpoints Provided:
# - /performance/stats: Get comprehensive performance statistics and optimization metrics
# - /performance/clear-cache: Clear all performance caches for fresh metrics collection
# - /performance/cache-stats: Get detailed cache performance statistics and analytics
#
# Integration Points:
# - Uses PerformanceOptimizer for metrics collection and cache management
# - Integrates with RouterBase pattern for consistent response formatting
# - Provides performance data for monitoring dashboards and optimization analysis
# - Supports system health monitoring through performance metrics

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from models import ApiError, StandardResponse
from performance_optimizer import performance_optimizer
from routing import get_router_service_factory

# Create router using RouterBase pattern for consistent performance endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("performance")
router = router_base.get_router()
router.tags = ["performance"]


@router.get("/performance/stats")
async def get_performance_stats() -> StandardResponse[Dict[str, Any]]:
    # Get comprehensive performance statistics including optimization metrics and memory usage
    # Returns detailed analytics for parallel execution, cache performance, and system optimization
    # Used by monitoring dashboards and performance analysis tools

    # Retrieve comprehensive performance summary from optimizer
    optimizer_stats = await performance_optimizer.get_performance_summary()

    # Compile performance data with timestamp for monitoring
    stats_data = {
        "optimization": optimizer_stats,
        "timestamp": datetime.now().isoformat(),
    }

    router_base.log_request("/performance/stats")
    return router_base.success_response(
        "/performance/stats",
        stats_data,
        "Performance statistics retrieved successfully",
    )


@router.post("/performance/clear-cache")
async def clear_performance_cache() -> StandardResponse[Dict[str, str]]:
    # Clear all performance caches and reset metrics for fresh performance analysis
    # Resets cache hit/miss counters and operation timing data
    # Used for performance testing and metrics reset operations
    try:
        # Reset optimizer performance metrics and cache statistics
        performance_optimizer.metrics.cache_hits = 0
        performance_optimizer.metrics.cache_misses = 0
        performance_optimizer.operation_times.clear()

        router_base.log_request("/performance/clear-cache")
        return router_base.success_response(
            "/performance/clear-cache",
            {"cache_status": "cleared"},
            "Performance caches cleared successfully",
        )
    except Exception as e:
        # Handle cache clearing errors with detailed error reporting
        router_base.router_logger.log_error(
            "/performance/clear-cache", e, "CACHE_CLEAR_ERROR"
        )
        return router_base.response_formatter.create_error_response(
            "Failed to clear caches",
            [ApiError(code="CACHE_CLEAR_ERROR", message=str(e))],
        )


@router.get("/performance/cache-stats")
async def get_cache_stats() -> StandardResponse[Dict[str, Any]]:
    # Get detailed cache performance statistics including hit/miss ratios and efficiency metrics
    # Returns comprehensive cache analytics for performance optimization analysis
    # Used for cache performance monitoring and optimization decision making
    try:
        # Retrieve detailed cache statistics from performance optimizer
        cache_stats = performance_optimizer.get_cache_statistics()

        # Compile cache data with timestamp for analytics tracking
        cache_data = {
            "optimizer_cache": cache_stats,
            "timestamp": datetime.now().isoformat(),
        }

        router_base.log_request("/performance/cache-stats")
        return router_base.success_response(
            "/performance/cache-stats",
            cache_data,
            "Cache statistics retrieved successfully",
        )
    except Exception as e:
        # Handle cache statistics retrieval errors with comprehensive error reporting
        router_base.router_logger.log_error(
            "/performance/cache-stats", e, "CACHE_STATS_ERROR"
        )
        return router_base.response_formatter.create_error_response(
            "Failed to get cache stats",
            [ApiError(code="CACHE_STATS_ERROR", message=str(e))],
        )
