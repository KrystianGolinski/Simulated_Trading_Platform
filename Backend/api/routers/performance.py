from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from performance_optimizer import performance_optimizer
from models import StandardResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("performance")
router = router_base.get_router()
router.tags = ["performance"]

@router.get("/performance/stats")
async def get_performance_stats() -> StandardResponse[Dict[str, Any]]:
    # Get performance stats
    # Get optimizer performance stats
    optimizer_stats = performance_optimizer.get_performance_summary()
    
    stats_data = {
        "optimization": optimizer_stats,
        "timestamp": datetime.now().isoformat()
    }
    
    router_base.router_logger.log_request("/performance/stats", {})
    response = router_base.response_formatter.create_success_response(stats_data, "Performance statistics retrieved successfully")
    router_base.router_logger.log_success("/performance/stats")
    return response

@router.post("/performance/clear-cache")
async def clear_performance_cache() -> StandardResponse[Dict[str, str]]:
    # Clear all performance caches
    try:
        # Reset optimizer metrics
        performance_optimizer.metrics.cache_hits = 0
        performance_optimizer.metrics.cache_misses = 0
        performance_optimizer.operation_times.clear()
        
        router_base.router_logger.log_request("/performance/clear-cache", {})
        response = router_base.response_formatter.create_success_response(
            {"cache_status": "cleared"},
            "Performance caches cleared successfully"
        )
        router_base.router_logger.log_success("/performance/clear-cache")
        return response
    except Exception as e:
        router_base.router_logger.log_error("/performance/clear-cache", e, "CACHE_CLEAR_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to clear caches",
            [ApiError(code="CACHE_CLEAR_ERROR", message=str(e))]
        )

@router.get("/performance/cache-stats")
async def get_cache_stats() -> StandardResponse[Dict[str, Any]]:
    # Get cache performance statistics
    try:
        cache_stats = performance_optimizer.get_cache_statistics()
        
        cache_data = {
            "optimizer_cache": cache_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        router_base.router_logger.log_request("/performance/cache-stats", {})
        response = router_base.response_formatter.create_success_response(cache_data, "Cache statistics retrieved successfully")
        router_base.router_logger.log_success("/performance/cache-stats")
        return response
    except Exception as e:
        router_base.router_logger.log_error("/performance/cache-stats", e, "CACHE_STATS_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to get cache stats",
            [ApiError(code="CACHE_STATS_ERROR", message=str(e))]
        )