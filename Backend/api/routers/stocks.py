from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime

from database import DatabaseManager, get_database

router = APIRouter(tags=["stocks"])

@router.get("/stocks")
async def get_stocks(db: DatabaseManager = Depends(get_database)) -> List[str]:
    # Get list of available stock symbols in DB
    return await db.get_available_stocks()

@router.get("/stocks/{symbol}/data")
async def get_stock_data(symbol: str, start_date: str, end_date: str, timeframe: str = "daily", db: DatabaseManager = Depends(get_database)) -> List[Dict[str, Any]]:
    # Get historical stock data
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    return await db.get_stock_data(symbol, start, end, timeframe)