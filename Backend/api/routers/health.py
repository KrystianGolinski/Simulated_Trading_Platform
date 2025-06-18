from fastapi import APIRouter, Depends

from database import DatabaseManager, get_database
from validation import SimulationValidator

router = APIRouter(tags=["health"])

@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Trading Platform API - Development Environment Ready"}

@router.get("/health")
async def health_check(db: DatabaseManager = Depends(get_database)):
    """Enhanced health check with database status and validation system"""
    try:
        db_health = await db.health_check()
        
        # Check validation system
        validator = SimulationValidator(db)
        validation_health = await validator.check_database_connection()
        
        overall_status = "healthy"
        if db_health["status"] != "healthy":
            overall_status = "degraded"
        elif not validation_health.is_valid:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "service": "trading-api",
            "database": db_health,
            "validation_system": {
                "status": "healthy" if validation_health.is_valid else "degraded",
                "errors": [error.dict() for error in validation_health.errors],
                "warnings": validation_health.warnings
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "trading-api",
            "error": str(e)
        }