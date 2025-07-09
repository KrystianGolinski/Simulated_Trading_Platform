# Stocks Router - Stock Data and Temporal Validation Endpoints
# This module provides comprehensive API endpoints for stock data access and temporal validation
# Key responsibilities:
# - Stock symbol listing and pagination for large datasets
# - Historical stock data retrieval with OHLCV data and date range filtering
# - Temporal validation for stock trading eligibility (IPO/delisting dates)
# - Stock metadata and temporal information management
# - Date range validation and data availability checking
# - Batch temporal validation for simulation preparation
# - Stock trading period eligibility assessment
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure and logging
# - Integration with StockDataRepository for comprehensive data access
# - Dependency injection for repository and service access
# - Pagination support for large stock datasets and historical data
# - Comprehensive temporal validation with IPO/delisting awareness
# - Error handling with detailed validation messages
# - Date format validation and parsing with proper error reporting
#
# Endpoints Provided:
# - /stocks: Get paginated list of available stock symbols
# - /stocks/{symbol}/date-range: Get available date range for specific stock
# - /stocks/{symbol}/data: Get historical OHLCV data with pagination
# - /stocks/validate-temporal: Validate symbols for trading period eligibility
# - /stocks/{symbol}/temporal-info: Get comprehensive temporal information
# - /stocks/check-tradeable: Check if stock was tradeable on specific date
# - /stocks/eligible-for-period: Get stocks eligible for trading period
#
# Integration Points:
# - Uses StockDataRepository for comprehensive stock data access
# - Integrates with temporal validation for simulation preparation
# - Supports RouterBase pattern for consistent response formatting
# - Provides stock data for simulation configuration and validation

from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends
from pydantic import BaseModel

from dependencies import get_stock_data_repository
from models import ApiError, PaginatedResponse, StandardResponse
from repositories.stock_data_repository import StockDataRepository
from routing import get_router_service_factory

# Create router using RouterBase pattern for consistent stock endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("stocks")
router = router_base.get_router()
router.tags = ["stocks"]


# Request models for temporal validation operations
class TemporalValidationRequest(BaseModel):
    symbols: List[str]
    start_date: str  # YYYY-MM-DD format for ISO date parsing
    end_date: str  # YYYY-MM-DD format for ISO date parsing


class StockTradeableRequest(BaseModel):
    symbol: str
    check_date: str  # YYYY-MM-DD format for ISO date parsing


# RouterBase pattern integration provides injected services:
# - validation_service: Configuration validation and error handling
# - response_formatter: Standardized response creation and pagination
# - router_logger: Comprehensive request/response logging with correlation


@router.get("/stocks")
async def get_stocks(
    page: int = 1,
    page_size: int = 100,
    stock_repo: StockDataRepository = Depends(get_stock_data_repository),
) -> PaginatedResponse[str]:
    # Get paginated list of all available stock symbols from the database
    # Supports large datasets with configurable pagination for efficient data retrieval
    # Returns alphabetically sorted stock symbols with pagination metadata
    router_base.log_request("/stocks", {"page": page, "page_size": page_size})

    # Validate pagination parameters for proper data retrieval
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 1000:
        raise ValueError("Page size must be between 1 and 1000")

    # Retrieve paginated stock symbols with total count for pagination metadata
    stocks, total_count = await stock_repo.get_available_stocks(
        page=page, page_size=page_size
    )

    # Use injected response formatter for pagination
    response = router_base.response_formatter.format_paginated_response(
        data=stocks,
        total_count=total_count,
        page=page,
        page_size=page_size,
        message="Successfully retrieved available stocks",
    )

    router_base.router_logger.log_success("/stocks", len(stocks))
    return response


@router.get("/stocks/{symbol}/date-range")
async def get_stock_date_range(
    symbol: str, stock_repo: StockDataRepository = Depends(get_stock_data_repository)
) -> StandardResponse[Dict[str, str]]:
    # Get the available date range for historical data of a specific stock symbol
    # Returns earliest and latest available dates for the stock in the database
    # Used for temporal validation and date range selection in client applications
    router_base.log_request(f"/stocks/{symbol}/date-range", {"symbol": symbol})

    result = await stock_repo.get_symbol_date_range(symbol)
    if not result:
        error_response = router_base.response_formatter.create_not_found_response(
            "Symbol", symbol, "symbol"
        )
        router_base.router_logger.log_error(
            f"/stocks/{symbol}/date-range",
            ValueError(f"Symbol {symbol} not found"),
            "SYMBOL_NOT_FOUND",
        )
        return error_response

    date_range = {
        "min_date": result["earliest_date"].strftime("%Y-%m-%d"),
        "max_date": result["latest_date"].strftime("%Y-%m-%d"),
    }

    return router_base.success_response(
        f"/stocks/{symbol}/date-range",
        date_range,
        f"Successfully retrieved date range for {symbol}",
    )


@router.get("/stocks/{symbol}/data")
async def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "daily",
    page: int = 1,
    page_size: int = 1000,
    stock_repo: StockDataRepository = Depends(get_stock_data_repository),
) -> PaginatedResponse[Dict[str, Any]]:
    # Get historical OHLCV stock data with pagination and date range filtering
    # Returns time-series stock data for specified symbol and date range with pagination support
    # Used for chart display, analysis, and simulation data preparation

    # Validate pagination parameters for efficient data retrieval
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    if page_size < 1 or page_size > 10000:
        raise ValueError("Page size must be between 1 and 10000")

    # Parse ISO date strings to date objects for repository operations
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()

    # Retrieve paginated historical stock data with comprehensive metadata
    data, total_count, date_range = await stock_repo.get_stock_data(
        symbol, start, end, timeframe, page=page, page_size=page_size
    )

    # Use injected response formatter for pagination
    router_base.log_request(
        f"/stocks/{symbol}/data",
        {"symbol": symbol, "start_date": start_date, "end_date": end_date},
    )

    response = router_base.response_formatter.format_paginated_response(
        data=data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        message=f"Successfully retrieved data for {symbol} from {start_date} to {end_date}",
        metadata={"symbol": symbol, "date_range": date_range},
    )

    router_base.router_logger.log_success(f"/stocks/{symbol}/data", len(data))
    return response


# Temporal validation endpoints for trading eligibility assessment
@router.post("/stocks/validate-temporal")
async def validate_stocks_for_period(
    request: TemporalValidationRequest,
    stock_repo: StockDataRepository = Depends(get_stock_data_repository),
) -> StandardResponse[Dict[str, Any]]:
    # Validate if stocks were trading during specified period with comprehensive temporal checks
    # Accounts for IPO dates, delisting dates, and trading suspensions for simulation eligibility
    # Returns categorized results with valid/invalid symbols and detailed error messages
    try:
        start_date = datetime.fromisoformat(request.start_date).date()
        end_date = datetime.fromisoformat(request.end_date).date()

        router_base.log_request(
            "/stocks/validate-temporal", {"symbols": len(request.symbols)}
        )

        if start_date > end_date:
            response = router_base.response_formatter.create_error_response(
                "Invalid date range: start_date must be before end_date",
                [
                    ApiError(
                        code="INVALID_DATE_RANGE",
                        message="Start date must be before end date",
                    )
                ],
            )
            router_base.router_logger.log_error(
                "/stocks/validate-temporal",
                Exception("Invalid date range"),
                "INVALID_DATE_RANGE",
            )
            return response

        validation_result = await stock_repo.validate_symbols_for_period(
            request.symbols, start_date, end_date
        )

        return router_base.success_response(
            "/stocks/validate-temporal",
            validation_result,
            f"Temporal validation completed for {len(request.symbols)} symbols",
            len(request.symbols),
        )

    except ValueError as e:
        router_base.router_logger.log_error(
            "/stocks/validate-temporal", e, "INVALID_DATE_FORMAT"
        )
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}",
            [ApiError(code="INVALID_DATE_FORMAT", message=str(e))],
        )
    except Exception as e:
        router_base.router_logger.log_error(
            "/stocks/validate-temporal", e, "VALIDATION_ERROR"
        )
        return router_base.response_formatter.create_error_response(
            f"Temporal validation failed: {str(e)}",
            [ApiError(code="VALIDATION_ERROR", message=str(e))],
        )


@router.get("/stocks/{symbol}/temporal-info")
async def get_stock_temporal_info(
    symbol: str, stock_repo: StockDataRepository = Depends(get_stock_data_repository)
) -> StandardResponse[Dict[str, Any]]:
    # Get comprehensive temporal information for a stock including IPO and delisting dates
    # Returns complete trading history metadata for temporal validation and analysis
    # Used for understanding stock trading eligibility and historical context
    temporal_info = await stock_repo.get_stock_temporal_info(symbol)

    router_base.log_request(f"/stocks/{symbol}/temporal-info", {"symbol": symbol})

    if not temporal_info:
        response = router_base.response_formatter.create_not_found_response(
            "Temporal information", symbol, "symbol"
        )
        router_base.router_logger.log_error(
            f"/stocks/{symbol}/temporal-info",
            Exception("Temporal info not found"),
            "TEMPORAL_INFO_NOT_FOUND",
        )
        return response

    return router_base.success_response(
        f"/stocks/{symbol}/temporal-info",
        temporal_info,
        f"Successfully retrieved temporal information for {symbol}",
    )


@router.post("/stocks/check-tradeable")
async def check_stock_tradeable(
    request: StockTradeableRequest,
    stock_repo: StockDataRepository = Depends(get_stock_data_repository),
) -> StandardResponse[Dict[str, Any]]:
    # Check if a stock was tradeable on a specific date with temporal context
    # Returns trading eligibility status with additional context for non-tradeable stocks
    # Provides IPO/delisting information when stock is not tradeable
    try:
        check_date = datetime.fromisoformat(request.check_date).date()

        is_tradeable = await stock_repo.validate_stock_tradeable(
            request.symbol, check_date
        )

        result = {
            "symbol": request.symbol.upper(),
            "check_date": request.check_date,
            "is_tradeable": is_tradeable,
        }

        # Add comprehensive temporal context for non-tradeable stocks
        if not is_tradeable:
            temporal_info = await stock_repo.get_stock_temporal_info(request.symbol)
            if temporal_info:
                result["temporal_context"] = {
                    "ipo_date": temporal_info.get("ipo_date"),
                    "listing_date": temporal_info.get("listing_date"),
                    "delisting_date": temporal_info.get("delisting_date"),
                    "trading_status": temporal_info.get("trading_status"),
                }

        router_base.log_request(
            "/stocks/check-tradeable",
            {"symbol": request.symbol, "check_date": request.check_date},
        )

        return router_base.success_response(
            "/stocks/check-tradeable",
            result,
            f"Checked tradeability of {request.symbol} on {request.check_date}",
        )

    except ValueError as e:
        router_base.router_logger.log_error(
            "/stocks/check-tradeable", e, "INVALID_DATE_FORMAT"
        )
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}",
            [ApiError(code="INVALID_DATE_FORMAT", message=str(e))],
        )
    except Exception as e:
        router_base.router_logger.log_error(
            "/stocks/check-tradeable", e, "VALIDATION_ERROR"
        )
        return router_base.response_formatter.create_error_response(
            f"Tradeability check failed: {str(e)}",
            [ApiError(code="VALIDATION_ERROR", message=str(e))],
        )


@router.get("/stocks/eligible-for-period")
async def get_eligible_stocks_for_period(
    start_date: str,
    end_date: str,
    stock_repo: StockDataRepository = Depends(get_stock_data_repository),
) -> StandardResponse[List[str]]:
    # Get comprehensive list of stocks eligible for trading during a specific period
    # Returns filtered stock list excluding stocks with IPO/delisting issues during the period
    # Used for simulation preparation and strategy backtesting with valid stock universe
    try:
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()

        router_base.log_request(
            "/stocks/eligible-for-period",
            {"start_date": start_date, "end_date": end_date},
        )

        if start_date_obj > end_date_obj:
            response = router_base.response_formatter.create_error_response(
                "Invalid date range: start_date must be before end_date",
                [
                    ApiError(
                        code="INVALID_DATE_RANGE",
                        message="Start date must be before end date",
                    )
                ],
            )
            router_base.router_logger.log_error(
                "/stocks/eligible-for-period",
                Exception("Invalid date range"),
                "INVALID_DATE_RANGE",
            )
            return response

        eligible_stocks = await stock_repo.get_eligible_stocks_for_period(
            start_date_obj, end_date_obj
        )

        return router_base.success_response(
            "/stocks/eligible-for-period",
            eligible_stocks,
            f"Found {len(eligible_stocks)} stocks eligible for period {start_date} to {end_date}",
            len(eligible_stocks),
        )

    except ValueError as e:
        router_base.router_logger.log_error(
            "/stocks/eligible-for-period", e, "INVALID_DATE_FORMAT"
        )
        return router_base.response_formatter.create_error_response(
            f"Invalid date format: {str(e)}",
            [ApiError(code="INVALID_DATE_FORMAT", message=str(e))],
        )
    except Exception as e:
        router_base.router_logger.log_error(
            "/stocks/eligible-for-period", e, "QUERY_ERROR"
        )
        return router_base.response_formatter.create_error_response(
            f"Failed to get eligible stocks: {str(e)}",
            [ApiError(code="QUERY_ERROR", message=str(e))],
        )
