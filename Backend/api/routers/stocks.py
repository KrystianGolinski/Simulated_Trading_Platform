from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime

from database import DatabaseManager, get_database
from response_models import StandardResponse, create_success_response, create_error_response, ApiError
from base_router import BaseRouter, DatabaseMixin

router = APIRouter(tags=["stocks"])

class StocksRouter(BaseRouter, DatabaseMixin):
    # Inherits from BaseRouter and DatabaseMixin - no additional functionality needed
    pass

stocks_router = StocksRouter()

@router.get("/stocks")
async def get_stocks(page: int = 1, page_size: int = 100, 
                    db: DatabaseManager = Depends(get_database)) -> StandardResponse:
    # Get list of available stock symbols in DB with pagination
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 1000:
        raise ValueError("Page size must be between 1 and 1000")
    
    result = await db.get_available_stocks(page=page, page_size=page_size)
    return stocks_router.create_success_with_metadata(result, "Successfully retrieved available stocks")

@router.get("/stocks/{symbol}/date-range")
async def get_stock_date_range(symbol: str, db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, str]]:
    # Get available date range for a specific stock
    result = await db.get_symbol_date_range(symbol)
    if not result:
        return stocks_router.create_not_found_response("Symbol", symbol, "symbol")
    
    date_range = {
        "min_date": result['earliest_date'].strftime('%Y-%m-%d'),
        "max_date": result['latest_date'].strftime('%Y-%m-%d')
    }
    
    return stocks_router.create_success_with_metadata(
        date_range,
        f"Successfully retrieved date range for {symbol}",
        symbol=symbol
    )

@router.get("/stocks/{symbol}/data")
async def get_stock_data(symbol: str, start_date: str, end_date: str, timeframe: str = "daily", 
                        page: int = 1, page_size: int = 1000, 
                        db: DatabaseManager = Depends(get_database)) -> StandardResponse:
    # Get historical stock data with pagination
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 10000:
        raise ValueError("Page size must be between 1 and 10000")
    
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    result = await db.get_stock_data(symbol, start, end, timeframe, page=page, page_size=page_size)
    return stocks_router.create_success_with_metadata(
        result, 
        f"Successfully retrieved data for {symbol} from {start_date} to {end_date}"
    )