from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime

from database import DatabaseManager, get_database
from response_models import StandardResponse, create_success_response, create_error_response, ApiError

router = APIRouter(tags=["stocks"])

@router.get("/stocks")
async def get_stocks(db: DatabaseManager = Depends(get_database)) -> StandardResponse[List[str]]:
    # Get list of available stock symbols in DB
    try:
        stocks = await db.get_available_stocks()
        return create_success_response(stocks, "Successfully retrieved available stocks")
    except Exception as e:
        return create_error_response(
            "Failed to retrieve stocks",
            [ApiError(code="STOCKS_FETCH_ERROR", message=str(e))]
        )

@router.get("/stocks/{symbol}/data")
async def get_stock_data(symbol: str, start_date: str, end_date: str, timeframe: str = "daily", db: DatabaseManager = Depends(get_database)) -> StandardResponse[List[Dict[str, Any]]]:
    # Get historical stock data
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        
        data = await db.get_stock_data(symbol, start, end, timeframe)
        return create_success_response(
            data, 
            f"Successfully retrieved {len(data)} data points for {symbol}",
            metadata={"symbol": symbol, "timeframe": timeframe, "start_date": start_date, "end_date": end_date}
        )
    except ValueError as e:
        return create_error_response(
            "Invalid date format",
            [ApiError(code="INVALID_DATE_FORMAT", message=str(e))]
        )
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve stock data for {symbol}",
            [ApiError(code="STOCK_DATA_FETCH_ERROR", message=str(e), field="symbol")]
        )