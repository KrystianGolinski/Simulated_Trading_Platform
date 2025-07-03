from fastapi import APIRouter, Depends
from typing import Dict, Any
import os
import time
from pathlib import Path

from database import DatabaseManager, get_database
from validation import SimulationValidator
from response_models import StandardResponse, create_success_response, create_error_response, ApiError
from base_router import BaseRouter

router = APIRouter(tags=["health"])

class HealthRouter(BaseRouter):
    # Health monitoring router with standardized patterns
    pass

health_router = HealthRouter()

async def check_cpp_engine_health() -> Dict[str, Any]:
    # Check if C++ engine is available and functional
    try:
        # Check if engine binary exists in expected locations
        engine_paths = [
            Path("/shared/trading_engine"),  # Docker shared volume
            Path("/app/cpp-engine/build/trading_engine"),  # Local build
        ]
        
        for engine_path in engine_paths:
            if engine_path.exists() and os.access(engine_path, os.X_OK):
                return {
                    "status": "healthy",
                    "engine_path": str(engine_path),
                    "executable": True
                }
        
        return {
            "status": "unhealthy",
            "engine_path": None,
            "executable": False,
            "error": "C++ engine binary not found or not executable"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def get_system_health() -> Dict[str, Any]:
    # Get system resource health metrics
    try:
        import shutil
        import psutil
        
        # Get disk usage
        disk_usage = shutil.disk_usage("/")
        disk_usage_pct = (disk_usage.used / disk_usage.total) * 100
        
        # Get memory usage
        memory = psutil.virtual_memory()
        
        return {
            "disk_usage_pct": round(disk_usage_pct, 2),
            "available_disk_gb": round(disk_usage.free / (1024**3), 2),
            "total_disk_gb": round(disk_usage.total / (1024**3), 2),
            "memory_usage_pct": memory.percent,
            "available_memory_mb": round(memory.available / (1024**2), 2),
            "total_memory_gb": round(memory.total / (1024**3), 2)
        }
    except ImportError:
        # psutil not available, return basic info
        try:
            import shutil
            disk_usage = shutil.disk_usage("/")
            disk_usage_pct = (disk_usage.used / disk_usage.total) * 100
            
            return {
                "disk_usage_pct": round(disk_usage_pct, 2),
                "available_disk_gb": round(disk_usage.free / (1024**3), 2),
                "total_disk_gb": round(disk_usage.total / (1024**3), 2),
                "memory_info": "psutil not available"
            }
        except Exception as e:
            return {
                "error": f"System health check failed: {str(e)}"
            }
    except Exception as e:
        return {
            "error": f"System health check failed: {str(e)}"
        }

@router.get("/")
async def root() -> StandardResponse[Dict[str, str]]:
    # Root endpoint
    return health_router.create_success_with_metadata(
        {"service": "Trading Platform API", "version": "1.0.0"},
        "Trading Platform API is running"
    )

@router.get("/health/ready")
async def readiness_check(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Kubernetes-style readiness probe - checks if service is ready to accept traffic
    try:
        # Quick database connection check
        db_health = await db.health_check()
        
        if db_health["status"] == "healthy":
            return create_success_response(
                {"ready": True, "database": "connected"},
                "Service ready to accept traffic"
            )
        else:
            return create_error_response(
                "Service not ready",
                [ApiError(code="NOT_READY", message="Database connection failed")]
            )
    except Exception as e:
        return create_error_response(
            "Readiness check failed",
            [ApiError(code="READINESS_ERROR", message=str(e))]
        )

@router.get("/health/live")
async def liveness_check() -> StandardResponse[Dict[str, Any]]:
    # Kubernetes-style liveness probe - checks if service is alive
    return create_success_response(
        {"alive": True, "timestamp": time.time()},
        "Service is alive"
    )

@router.get("/health")
async def health_check(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Health check with all system components
    try:
        start_time = time.time()
        
        # Check database connection
        db_health = await db.health_check()
        
        # Check validation system
        validator = SimulationValidator(db)
        validation_health = await validator.check_database_connection()
        
        # Check C++ engine availability
        cpp_engine_health = await check_cpp_engine_health()
        
        # Check disk space and memory
        system_health = get_system_health()
        
        # Determine overall status
        overall_status = "healthy"
        health_issues = []
        
        if db_health["status"] != "healthy":
            overall_status = "degraded"
            health_issues.append("Database connection issues")
            
        if not validation_health.is_valid:
            overall_status = "degraded"
            health_issues.append("Validation system errors")
            
        if cpp_engine_health["status"] != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"
            health_issues.append("C++ engine unavailable")
            
        if system_health["disk_usage_pct"] > 90 or system_health["available_memory_mb"] < 100:
            if overall_status == "healthy":
                overall_status = "degraded"
            health_issues.append("System resources low")
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
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
                    "errors": [error.model_dump() for error in validation_health.errors],
                    "warnings": validation_health.warnings
                },
                "cpp_engine": cpp_engine_health,
                "system_resources": system_health
            }
        }
        
        if overall_status == "healthy":
            return create_success_response(health_data, "All systems healthy")
        else:
            return create_error_response(
                f"System health check failed: {', '.join(health_issues)}",
                [ApiError(code="HEALTH_CHECK_FAILED", message=f"System status: {overall_status}")]
            )
    except Exception as e:
        return create_error_response(
            "Health check failed",
            [ApiError(code="HEALTH_CHECK_ERROR", message=str(e))]
        )

@router.get("/health/dashboard")
async def health_dashboard(db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Health dashboard with metrics and status
    try:
        dashboard_data = {
            "service_info": {
                "name": "Trading Platform API",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "health_endpoints": {
                "main_health": "/health",
                "readiness": "/health/ready", 
                "liveness": "/health/live",
                "dashboard": "/health/dashboard"
            },
            "monitoring_info": {
                "health_check_interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s"
            }
        }
        
        # Get health data
        health_result = await health_check(db)
        if health_result.data:
            dashboard_data["current_health"] = health_result.data
        
        return create_success_response(
            dashboard_data,
            "Health dashboard data retrieved successfully"
        )
    except Exception as e:
        return create_error_response(
            "Failed to generate health dashboard",
            [ApiError(code="DASHBOARD_ERROR", message=str(e))]
        )
