from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

from dependencies import get_stock_data_repository
from repositories.stock_data_repository import StockDataRepository
from models import StandardResponse, PaginatedResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("stocks")
router = router_base.get_router()
router.tags = ["stocks"]

# Request models for temporal validation
class TemporalValidationRequest(BaseModel):
    symbols: List[str]
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format

class StockTradeableRequest(BaseModel):
    symbol: str
    check_date: str  # YYYY-MM-DD format

# Using RouterBase pattern with service injection
# router_base provides injected services: validation_service, response_formatter, router_logger

@router.get("/stocks")
async def get_stocks(page: int = 1, page_size: int = 100, 
                    stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> PaginatedResponse[str]:
    # Retrieves a paginated list of all available stock symbols from the database.
    router_base.router_logger.log_request("/stocks", {"page": page, "page_size": page_size})
    
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 1000:
        raise ValueError("Page size must be between 1 and 1000")
    
    stocks, total_count = await stock_repo.get_available_stocks(page=page, page_size=page_size)
    
    # Use injected response formatter for pagination
    response = router_base.response_formatter.format_paginated_response(
        data=stocks,
        total_count=total_count,
        page=page,
        page_size=page_size,
        message="Successfully retrieved available stocks"
    )
    
    router_base.router_logger.log_success("/stocks", len(stocks))
    return response

@router.get("/stocks/{symbol}/date-range")
async def get_stock_date_range(symbol: str, stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> StandardResponse[Dict[str, str]]:
    # Gets the earliest and latest date of available historical data for a specific stock symbol.
    router_base.router_logger.log_request(f"/stocks/{symbol}/date-range", {"symbol": symbol})
    
    result = await stock_repo.get_symbol_date_range(symbol)
    if not result:
        error_response = router_base.response_formatter.create_not_found_response(
            "Symbol", symbol, "symbol"
        )
        router_base.router_logger.log_error(f"/stocks/{symbol}/date-range", 
                                          ValueError(f"Symbol {symbol} not found"), "SYMBOL_NOT_FOUND")
        return error_response
    
    date_range = {
        "min_date": result['earliest_date'].strftime('%Y-%m-%d'),
        "max_date": result['latest_date'].strftime('%Y-%m-%d')
    }
    
    response = router_base.response_formatter.create_success_response(
        date_range,
        f"Successfully retrieved date range for {symbol}"
    )
    
    router_base.router_logger.log_success(f"/stocks/{symbol}/date-range")
    return response

@router.get("/stocks/{symbol}/data")
async def get_stock_data(symbol: str, start_date: str, end_date: str, timeframe: str = "daily", 
                        page: int = 1, page_size: int = 1000, 
                        stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> PaginatedResponse[Dict[str, Any]]:
    # Get historical stock data
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 10000:
        raise ValueError("Page size must be between 1 and 10000")
    
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    data, total_count, date_range = await stock_repo.get_stock_data(symbol, start, end, timeframe, page=page, page_size=page_size)
    
    # Use injected response formatter for pagination
    router_base.router_logger.log_request(f"/stocks/{symbol}/data", {"symbol": symbol, "start_date": start_date, "end_date": end_date})
    
    response = router_base.response_formatter.format_paginated_response(
        data=data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        message=f"Successfully retrieved data for {symbol} from {start_date} to {end_date}",
        metadata={'symbol': symbol, 'date_range': date_range}
    )
    
    router_base.router_logger.log_success(f"/stocks/{symbol}/data", len(data))
    return response

# Temporal validation endpoints
@router.post("/stocks/validate-temporal")
async def validate_stocks_for_period(request: TemporalValidationRequest, 
                                   stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> StandardResponse[Dict[str, Any]]:
    # Validate if stocks were trading during specified period
    # Accounts for IPO dates, delisting dates, and trading suspensions
    try:
        start_date = datetime.fromisoformat(request.start_date).date()
        end_date = datetime.fromisoformat(request.end_date).date()
        
        router_base.router_logger.log_request("/stocks/validate-temporal", {"symbols": len(request.symbols)})
        
        if start_date > end_date:
            response = router_base.response_formatter.create_error_response(
                "Invalid date range: start_date must be before end_date",
                [ApiError(code="INVALID_DATE_RANGE", message="Start date must be before end date")]
            )
            router_base.router_logger.log_error("/stocks/validate-temporal", Exception("Invalid date range"), "INVALID_DATE_RANGE")
            return response
        
        validation_result = await stock_repo.validate_symbols_for_period(request.symbols, start_date, end_date)
        
        response = router_base.response_formatter.create_success_response(
            validation_result,
            f"Temporal validation completed for {len(request.symbols)} symbols"
        )
        router_base.router_logger.log_success("/stocks/validate-temporal", len(request.symbols))
        return response
        
    except ValueError as e:
        router_base.router_logger.log_error("/stocks/validate-temporal", e, "INVALID_DATE_FORMAT")
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}", [ApiError(code="INVALID_DATE_FORMAT", message=str(e))]
        )
    except Exception as e:
        router_base.router_logger.log_error("/stocks/validate-temporal", e, "VALIDATION_ERROR")
        return router_base.response_formatter.create_error_response(
            f"Temporal validation failed: {str(e)}", [ApiError(code="VALIDATION_ERROR", message=str(e))]
        )

@router.get("/stocks/{symbol}/temporal-info")
async def get_stock_temporal_info(symbol: str, stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> StandardResponse[Dict[str, Any]]:
    # Get temporal information for a stock (IPO, delisting, trading periods)
    temporal_info = await stock_repo.get_stock_temporal_info(symbol)
    
    router_base.router_logger.log_request(f"/stocks/{symbol}/temporal-info", {"symbol": symbol})
    
    if not temporal_info:
        response = router_base.response_formatter.create_not_found_response(
            "Temporal information", symbol, "symbol"
        )
        router_base.router_logger.log_error(f"/stocks/{symbol}/temporal-info", 
                                          Exception("Temporal info not found"), "TEMPORAL_INFO_NOT_FOUND")
        return response
    
    response = router_base.response_formatter.create_success_response(
        temporal_info,
        f"Successfully retrieved temporal information for {symbol}"
    )
    router_base.router_logger.log_success(f"/stocks/{symbol}/temporal-info")
    return response

@router.post("/stocks/check-tradeable")
async def check_stock_tradeable(request: StockTradeableRequest, 
                              stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> StandardResponse[Dict[str, Any]]:
    # Check if a stock was tradeable on a specific date
    try:
        check_date = datetime.fromisoformat(request.check_date).date()
        
        is_tradeable = await stock_repo.validate_stock_tradeable(request.symbol, check_date)
        
        result = {
            "symbol": request.symbol.upper(),
            "check_date": request.check_date,
            "is_tradeable": is_tradeable
        }
        
        # Add temporal context if not tradeable
        if not is_tradeable:
            temporal_info = await stock_repo.get_stock_temporal_info(request.symbol)
            if temporal_info:
                result["temporal_context"] = {
                    "ipo_date": temporal_info.get("ipo_date"),
                    "listing_date": temporal_info.get("listing_date"),
                    "delisting_date": temporal_info.get("delisting_date"),
                    "trading_status": temporal_info.get("trading_status")
                }
        
        router_base.router_logger.log_request("/stocks/check-tradeable", {"symbol": request.symbol, "check_date": request.check_date})
        
        response = router_base.response_formatter.create_success_response(
            result,
            f"Checked tradeability of {request.symbol} on {request.check_date}"
        )
        router_base.router_logger.log_success("/stocks/check-tradeable")
        return response
        
    except ValueError as e:
        router_base.router_logger.log_error("/stocks/check-tradeable", e, "INVALID_DATE_FORMAT")
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}", [ApiError(code="INVALID_DATE_FORMAT", message=str(e))]
        )
    except Exception as e:
        router_base.router_logger.log_error("/stocks/check-tradeable", e, "VALIDATION_ERROR")
        return router_base.response_formatter.create_error_response(
            f"Tradeability check failed: {str(e)}", [ApiError(code="VALIDATION_ERROR", message=str(e))]
        )

@router.get("/stocks/eligible-for-period")
async def get_eligible_stocks_for_period(start_date: str, end_date: str, 
                                       stock_repo: StockDataRepository = Depends(get_stock_data_repository)) -> StandardResponse[List[str]]:
    # Get stocks that were eligible for trading during a specific period
    try:
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()
        
        router_base.router_logger.log_request("/stocks/eligible-for-period", {"start_date": start_date, "end_date": end_date})
        
        if start_date_obj > end_date_obj:
            response = router_base.response_formatter.create_error_response(
                "Invalid date range: start_date must be before end_date",
                [ApiError(code="INVALID_DATE_RANGE", message="Start date must be before end date")]
            )
            router_base.router_logger.log_error("/stocks/eligible-for-period", Exception("Invalid date range"), "INVALID_DATE_RANGE")
            return response
        
        eligible_stocks = await stock_repo.get_eligible_stocks_for_period(start_date_obj, end_date_obj)
        
        response = router_base.response_formatter.create_success_response(
            eligible_stocks,
            f"Found {len(eligible_stocks)} stocks eligible for period {start_date} to {end_date}"
        )
        router_base.router_logger.log_success("/stocks/eligible-for-period", len(eligible_stocks))
        return response
        
    except ValueError as e:
        router_base.router_logger.log_error("/stocks/eligible-for-period", e, "INVALID_DATE_FORMAT")
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}", [ApiError(code="INVALID_DATE_FORMAT", message=str(e))]
        )
    except Exception as e:
        router_base.router_logger.log_error("/stocks/eligible-for-period", e, "QUERY_ERROR")
        return router_base.response_formatter.create_error_response(
            f"Failed to get eligible stocks: {str(e)}", [ApiError(code="QUERY_ERROR", message=str(e))]
        )