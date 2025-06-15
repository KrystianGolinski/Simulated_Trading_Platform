from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import DatabaseManager, get_database
from typing import List, Dict, Any

app = FastAPI(
    title="Trading Platform API",
    description="FastAPI backend for the simulated trading platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await get_database()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    from database import db_manager
    await db_manager.disconnect()

@app.get("/")
async def root():
    return {"message": "Trading Platform API - Development Environment Ready"}

@app.get("/health")
async def health_check(db: DatabaseManager = Depends(get_database)):
    """Enhanced health check with database status"""
    db_health = await db.health_check()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "service": "trading-api",
        "database": db_health
    }

@app.get("/stocks")
async def get_stocks(db: DatabaseManager = Depends(get_database)) -> List[str]:
    """Get list of available stock symbols"""
    return await db.get_available_stocks()

@app.get("/stocks/{symbol}/data")
async def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "daily",
    db: DatabaseManager = Depends(get_database)
) -> List[Dict[str, Any]]:
    """Get historical stock data"""
    from datetime import datetime
    
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    return await db.get_stock_data(symbol, start, end, timeframe)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)