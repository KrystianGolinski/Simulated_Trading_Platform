from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

from database import DatabaseManager, get_database
from response_models import StandardResponse, PaginatedResponse, create_success_response, create_error_response, create_paginated_response, ApiError
from base_router import BaseRouter, DatabaseMixin

router = APIRouter(tags=["stocks"])

# Request models for temporal validation
class TemporalValidationRequest(BaseModel):
    symbols: List[str]
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format

class StockTradeableRequest(BaseModel):
    symbol: str
    check_date: str  # YYYY-MM-DD format

class StocksRouter(BaseRouter, DatabaseMixin):
    # Inherits from BaseRouter and DatabaseMixin
    pass

stocks_router = StocksRouter()

@router.get("/stocks")
async def get_stocks(page: int = 1, page_size: int = 100, 
                    db: DatabaseManager = Depends(get_database)) -> PaginatedResponse[str]:
    # Get list of available stock symbols in DB
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 1000:
        raise ValueError("Page size must be between 1 and 1000")
    
    stocks, total_count = await db.get_available_stocks(page=page, page_size=page_size)
    
    # Use pagination
    return create_paginated_response(
        data=stocks,
        page=page,
        page_size=page_size,
        total_count=total_count,
        message="Successfully retrieved available stocks"
    )

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
                        db: DatabaseManager = Depends(get_database)) -> PaginatedResponse[Dict[str, Any]]:
    # Get historical stock data
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 10000:
        raise ValueError("Page size must be between 1 and 10000")
    
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    data, total_count, date_range = await db.get_stock_data(symbol, start, end, timeframe, page=page, page_size=page_size)
    
    # Use pagination 
    return create_paginated_response(
        data=data,
        page=page,
        page_size=page_size,
        total_count=total_count,
        message=f"Successfully retrieved data for {symbol} from {start_date} to {end_date}",
        metadata={'symbol': symbol, 'date_range': date_range}
    )

# Temporal validation endpoints
@router.post("/stocks/validate-temporal")
async def validate_stocks_for_period(request: TemporalValidationRequest, 
                                   db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Validate if stocks were trading during specified period
    # Accounts for IPO dates, delisting dates, and trading suspensions
    try:
        start_date = datetime.fromisoformat(request.start_date).date()
        end_date = datetime.fromisoformat(request.end_date).date()
        
        if start_date > end_date:
            return create_error_response(
                "Invalid date range: start_date must be before end_date",
                error_code="INVALID_DATE_RANGE"
            )
        
        validation_result = await db.validate_symbols_for_period(request.symbols, start_date, end_date)
        
        return create_success_response(
            validation_result,
            f"Temporal validation completed for {len(request.symbols)} symbols"
        )
        
    except ValueError as e:
        return create_error_response(f"Invalid date format: {str(e)}", error_code="INVALID_DATE_FORMAT")
    except Exception as e:
        return create_error_response(f"Temporal validation failed: {str(e)}", error_code="VALIDATION_ERROR")

@router.get("/stocks/{symbol}/temporal-info")
async def get_stock_temporal_info(symbol: str, db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Get temporal information for a stock (IPO, delisting, trading periods)
    temporal_info = await db.get_stock_temporal_info(symbol)
    
    if not temporal_info:
        return stocks_router.create_not_found_response("Temporal information", symbol, "symbol")
    
    return stocks_router.create_success_with_metadata(
        temporal_info,
        f"Successfully retrieved temporal information for {symbol}",
        symbol=symbol
    )

@router.post("/stocks/check-tradeable")
async def check_stock_tradeable(request: StockTradeableRequest, 
                              db: DatabaseManager = Depends(get_database)) -> StandardResponse[Dict[str, Any]]:
    # Check if a stock was tradeable on a specific date
    try:
        check_date = datetime.fromisoformat(request.check_date).date()
        
        is_tradeable = await db.validate_stock_tradeable(request.symbol, check_date)
        
        result = {
            "symbol": request.symbol.upper(),
            "check_date": request.check_date,
            "is_tradeable": is_tradeable
        }
        
        # Add temporal context if not tradeable
        if not is_tradeable:
            temporal_info = await db.get_stock_temporal_info(request.symbol)
            if temporal_info:
                result["temporal_context"] = {
                    "ipo_date": temporal_info.get("ipo_date"),
                    "listing_date": temporal_info.get("listing_date"),
                    "delisting_date": temporal_info.get("delisting_date"),
                    "trading_status": temporal_info.get("trading_status")
                }
        
        return create_success_response(
            result,
            f"Checked tradeability of {request.symbol} on {request.check_date}"
        )
        
    except ValueError as e:
        return create_error_response(f"Invalid date format: {str(e)}", error_code="INVALID_DATE_FORMAT")
    except Exception as e:
        return create_error_response(f"Tradeability check failed: {str(e)}", error_code="VALIDATION_ERROR")

@router.get("/stocks/eligible-for-period")
async def get_eligible_stocks_for_period(start_date: str, end_date: str, 
                                       db: DatabaseManager = Depends(get_database)) -> StandardResponse[List[str]]:
    # Get stocks that were eligible for trading during a specific period
    try:
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()
        
        if start_date_obj > end_date_obj:
            return create_error_response(
                "Invalid date range: start_date must be before end_date",
                error_code="INVALID_DATE_RANGE"
            )
        
        eligible_stocks = await db.get_eligible_stocks_for_period(start_date_obj, end_date_obj)
        
        return create_success_response(
            eligible_stocks,
            f"Found {len(eligible_stocks)} stocks eligible for period {start_date} to {end_date}"
        )
        
    except ValueError as e:
        return create_error_response(f"Invalid date format: {str(e)}", error_code="INVALID_DATE_FORMAT")
    except Exception as e:
        return create_error_response(f"Failed to get eligible stocks: {str(e)}", error_code="QUERY_ERROR")