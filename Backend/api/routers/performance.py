from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from database import DatabaseManager, get_database
from performance_optimizer import performance_optimizer

router = APIRouter(tags=["performance"])

@router.get("/performance/stats")
async def get_performance_stats(db: DatabaseManager = Depends(get_database)):
    # Get performance stats
    try:
        # Get optimizer performance stats
        optimizer_stats = performance_optimizer.get_performance_summary()
        
        # Get database performance stats
        db_perf_stats = await db.get_performance_stats()
        
        return {
            "optimization": optimizer_stats,
            "database": db_perf_stats,
            "timestamp": performance_optimizer.operation_times.get("performance_stats", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@router.post("/performance/clear-cache")
async def clear_performance_cache(db: DatabaseManager = Depends(get_database)):
    # Clear all performance caches
    try:
        # Clear database cache
        await db.clear_cache()
        
        # Reset optimizer metrics
        performance_optimizer.metrics = performance_optimizer.PerformanceMetrics()
        performance_optimizer.operation_times.clear()
        
        return {"message": "Performance caches cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear caches: {str(e)}")

@router.get("/performance/cache-stats")
async def get_cache_stats(db: DatabaseManager = Depends(get_database)):
    # Get cache performance statistics
    try:
        cache_stats = performance_optimizer.get_cache_statistics()
        db_perf = await db.get_performance_stats()
        
        return {
            "optimizer_cache": cache_stats,
            "database_cache": db_perf.get("cache_stats", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")