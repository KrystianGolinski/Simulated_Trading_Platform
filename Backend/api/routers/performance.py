from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from database import DatabaseManager, get_database
from performance_optimizer import performance_optimizer
from response_models import StandardResponse, create_success_response, create_error_response, ApiError
from base_router import BaseRouter

router = APIRouter(tags=["performance"])

class PerformanceRouter(BaseRouter):
    # Inherits from BaseRouter - no additional functionality needed
    pass

performance_router = PerformanceRouter()

@router.get("/performance/stats")
async def get_performance_stats(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Get performance stats
    # Get optimizer performance stats
    optimizer_stats = performance_optimizer.get_performance_summary()
    
    # Get database performance stats
    db_perf_stats = await db.get_performance_stats()
    
    stats_data = {
        "optimization": optimizer_stats,
        "database": db_perf_stats,
        "timestamp": performance_optimizer.operation_times.get("performance_stats", [])
    }
    
    return performance_router.create_success_with_metadata(stats_data, "Performance statistics retrieved successfully")

@router.post("/performance/clear-cache")
async def clear_performance_cache(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, str]]:
    # Clear all performance caches
    try:
        # Clear database cache
        await db.clear_cache()
        
        # Reset optimizer metrics
        performance_optimizer.metrics = performance_optimizer.PerformanceMetrics()
        performance_optimizer.operation_times.clear()
        
        return create_success_response(
            {"cache_status": "cleared"},
            "Performance caches cleared successfully"
        )
    except Exception as e:
        return create_error_response(
            "Failed to clear caches",
            [ApiError(code="CACHE_CLEAR_ERROR", message=str(e))]
        )

@router.get("/performance/cache-stats")
async def get_cache_stats(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Get cache performance statistics
    try:
        cache_stats = performance_optimizer.get_cache_statistics()
        db_perf = await db.get_performance_stats()
        
        cache_data = {
            "optimizer_cache": cache_stats,
            "database_cache": db_perf.get("cache_stats", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        return create_success_response(cache_data, "Cache statistics retrieved successfully")
    except Exception as e:
        return create_error_response(
            "Failed to get cache stats",
            [ApiError(code="CACHE_STATS_ERROR", message=str(e))]
        )