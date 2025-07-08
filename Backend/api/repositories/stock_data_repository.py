# Stock Data Repository - Comprehensive Stock Data Access Layer
# This module provides comprehensive data access capabilities for stock-related operations in the Trading Platform
# Key responsibilities:
# - Stock symbol validation and existence checking with caching
# - Historical stock price data retrieval with pagination support
# - Temporal validation for stock trading eligibility (IPO/delisting dates)
# - Batch operations for efficient multi-symbol data processing
# - Date range validation and data coverage analysis
# - Stock metadata and temporal information management
# - Comprehensive caching integration for performance optimization
# - Error handling with graceful fallbacks and detailed logging
#
# Architecture Features:
# - Repository pattern for clean data access abstraction
# - Integration with QueryExecutor for raw database operations
# - CacheManager integration for multi-tiered caching strategy
# - Batch operations optimized for parallel simulation processing
# - Temporal validation using database functions for trading eligibility
# - Pagination support for large datasets and memory efficiency
# - Comprehensive error handling with detailed context logging
# - Type-safe return values with structured data formats
#
# Data Operations:
# - Stock symbol listing with pagination
# - Historical OHLCV data retrieval with date range filtering
# - Multi-symbol batch data operations for parallel processing
# - Symbol existence validation with caching
# - Date range coverage analysis and data quality checks
# - Temporal validation for IPO and delisting dates
# - Trading eligibility checks for specific dates and periods
#
# Caching Strategy:
# - Symbol existence validation cached for performance
# - Stock data cached with TTL-based expiration
# - Date range information cached for temporal validation
# - Stocks list cached for pagination performance

from typing import Optional, List, Dict, Any, Tuple
import logging
from datetime import date

from db_components.query_executor import QueryExecutor
from db_components.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class StockDataRepository:
    # Comprehensive stock data access repository with caching and temporal validation
    # Provides optimized data access patterns for stock price data, symbol validation, and trading eligibility
    # Integrates with db_components for query execution and performance optimization
    
    def __init__(self, query_executor: QueryExecutor, cache_manager: CacheManager):
        self.query_executor = query_executor
        self.cache_manager = cache_manager
    
    async def get_available_stocks(self, page: int = 1, page_size: int = 100) -> Tuple[List[str], int]:
        # Get paginated list of available stock symbols from the database
        # Implements caching for performance optimization and supports pagination for large datasets
        # Returns tuple of (stock_symbols_list, total_count) for pagination metadata
        cache_key = f'available_stocks_{page}_{page_size}'
        
        # Check cache first to avoid database query for frequently requested pages
        cached_result = self.cache_manager.get_stocks_list(cache_key)
        if cached_result:
            return cached_result['data'], cached_result['total_count']
        
        # Calculate offset for pagination using standard pagination formula
        offset = (page - 1) * page_size
        
        # Get total count of distinct symbols for pagination metadata
        count_query = "SELECT COUNT(DISTINCT symbol) as total FROM stock_prices_daily"
        count_result = await self.query_executor.execute_query(count_query)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get paginated results with alphabetical ordering for consistency
        query = """
            SELECT DISTINCT symbol 
            FROM stock_prices_daily 
            ORDER BY symbol
            LIMIT $1 OFFSET $2
        """
        results = await self.query_executor.execute_query(query, page_size, offset)
        stocks = [row['symbol'] for row in results]
        
        # Cache the results for performance optimization with structured data format
        cache_data = {'data': stocks, 'total_count': total_count}
        self.cache_manager.set_stocks_list(cache_key, cache_data)
        total_pages = (total_count + page_size - 1) // page_size
        logger.debug(f"Fetched and cached {len(stocks)} available stocks (page {page}/{total_pages})")
        
        return stocks, total_count
    
    async def get_stock_data(self, symbol: str, start_date: date, end_date: date, timeframe: str = 'daily', 
                           page: int = 1, page_size: int = 1000) -> Tuple[List[Dict[str, Any]], int, Dict[str, str]]:
        # Get historical OHLCV stock data with pagination and caching support
        # Retrieves time-series data for specified symbol and date range with performance optimization
        # Returns tuple of (ohlcv_data_list, total_count, date_range_info) for comprehensive response
        cache_key = f"{symbol}_{start_date}_{end_date}_{timeframe}_{page}_{page_size}"
        
        # Check cache first to avoid database query for recently requested data
        cached_result = self.cache_manager.get_stock_data(cache_key)
        if cached_result:
            return cached_result['data'], cached_result['total_count'], cached_result['date_range']
        
        # Validate and select appropriate table based on timeframe
        if timeframe == 'daily':
            table = 'stock_prices_daily'
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Calculate offset for pagination using standard pagination formula
        offset = (page - 1) * page_size
        
        # Get total count of records for this symbol and date range for pagination metadata
        count_query = f"""
            SELECT COUNT(*) as total
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
        """
        count_result = await self.query_executor.execute_query(count_query, symbol, start_date, end_date)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get paginated OHLCV data with chronological ordering for time-series analysis
        query = f"""
            SELECT time, symbol, open, high, low, close, volume
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
            ORDER BY time ASC
            LIMIT $4 OFFSET $5
        """
        
        data = await self.query_executor.execute_query(query, symbol, start_date, end_date, page_size, offset)
        
        # Create date range metadata for API response
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Cache the complete result set for performance optimization
        cache_data = {
            'data': data,
            'total_count': total_count,
            'date_range': date_range
        }
        self.cache_manager.set_stock_data(cache_key, cache_data)
        total_pages = (total_count + page_size - 1) // page_size
        logger.debug(f"Fetched and cached stock data: {symbol} {start_date} to {end_date} page {page}/{total_pages} ({len(data)} records)")
        
        return data, total_count, date_range
    
    async def get_stock_data_batch(self, symbols: List[str], start_date: date, end_date: date, timeframe: str = 'daily') -> Dict[str, List[Dict[str, Any]]]:
        # Get historical stock data for multiple symbols in a single optimized query
        # Efficiently retrieves data for multiple symbols for parallel simulation processing
        # Returns dictionary mapping symbol to list of OHLCV records
        if not symbols:
            return {}
        
        # Create dynamic placeholders for IN clause to support variable symbol count
        placeholders = ','.join(f'${i+1}' for i in range(len(symbols)))
        
        table_name = 'stock_prices_daily'
        
        # Optimized batch query for multiple symbols with date range filtering
        query = f"""
            SELECT symbol, time, open, high, low, close, volume 
            FROM {table_name}
            WHERE symbol IN ({placeholders})
            AND time BETWEEN ${len(symbols)+1} AND ${len(symbols)+2}
            ORDER BY symbol, time
        """
        
        try:
            # Execute batch query with normalized symbol case for consistency
            results = await self.query_executor.execute_query(query, *[s.upper() for s in symbols], start_date, end_date)
            
            # Group results by symbol for structured response format
            symbol_data = {}
            for row in results:
                symbol = row['symbol']
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                symbol_data[symbol].append(row)
            
            # Ensure all requested symbols are represented with empty lists for missing data
            for symbol in symbols:
                if symbol.upper() not in symbol_data:
                    symbol_data[symbol.upper()] = []
            
            return symbol_data
            
        except Exception as e:
            logger.error(f"Error fetching batch stock data for {symbols}: {e}")
            # Return empty data structure for all symbols in case of error
            return {symbol.upper(): [] for symbol in symbols}
    
    async def validate_symbol_exists(self, symbol: str) -> bool:
        # Validate if a stock symbol exists in the database with caching for performance
        # Uses normalized uppercase symbol for consistent validation
        # Returns boolean indicating symbol existence
        cache_key = f"symbol_exists_{symbol.upper()}"
        
        # Check cache first to avoid database query for recently validated symbols
        cached_result = self.cache_manager.get_validation_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Query database for symbol existence using count query for efficiency
        query = """
            SELECT COUNT(*) as count
            FROM stock_prices_daily 
            WHERE symbol = $1
        """
        try:
            results = await self.query_executor.execute_query(query, symbol.upper())
            exists = results[0]['count'] > 0 if results else False
            
            # Cache the validation result for performance optimization
            self.cache_manager.set_validation_result(cache_key, exists)
            logger.debug(f"Validated and cached symbol existence: {symbol} = {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking symbol {symbol}: {e}")
            # Return False on error to avoid invalid symbol usage
            return False
    
    async def validate_multiple_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        # Validate multiple symbols in a single optimized database query
        # More efficient than individual symbol validation for batch operations
        # Returns dictionary mapping symbol to existence boolean
        if not symbols:
            return {}
        
        # Create dynamic placeholders for IN clause to support variable symbol count
        placeholders = ','.join(f'${i+1}' for i in range(len(symbols)))
        query = f"""
            SELECT DISTINCT symbol
            FROM stock_prices_daily 
            WHERE symbol IN ({placeholders})
        """
        
        try:
            # Execute batch validation query with normalized symbol case
            results = await self.query_executor.execute_query(query, *[s.upper() for s in symbols])
            existing_symbols = {row['symbol'] for row in results}
            
            # Create validation result mapping for all requested symbols
            return {symbol.upper(): symbol.upper() in existing_symbols for symbol in symbols}
        except Exception as e:
            # Let concurrent access errors propagate so QueryExecutor can retry
            if "operation is in progress" in str(e):
                raise
            # Log and handle other errors, return False for safety
            logger.error(f"Error validating symbols {symbols}: {e}")
            return {symbol.upper(): False for symbol in symbols}
    
    async def get_symbol_date_range(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Get the available date range for a symbol including earliest/latest dates and record count
        # Used for temporal validation and data availability analysis
        # Returns dictionary with date range metadata or None if no data exists
        cache_key = f"date_range_{symbol.upper()}"
        
        # Check cache first to avoid database query for recently requested date ranges
        cached_result = self.cache_manager.get_date_range(cache_key)
        if cached_result:
            return cached_result
        
        # Query for comprehensive date range statistics including record count
        query = """
            SELECT 
                MIN(time) as earliest_date,
                MAX(time) as latest_date,
                COUNT(*) as total_records
            FROM stock_prices_daily 
            WHERE symbol = $1
        """
        try:
            results = await self.query_executor.execute_query(query, symbol.upper())
            result = results[0] if results and results[0]['total_records'] > 0 else None
            
            # Cache the date range result for performance optimization
            self.cache_manager.set_date_range(cache_key, result)
            logger.debug(f"Fetched and cached date range for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Error getting date range for {symbol}: {e}")
            return None
    
    async def validate_date_range_has_data(self, symbol: str, start_date: date, end_date: date) -> Dict[str, Any]:
        # Validate data availability and coverage for symbol in specified date range
        # Analyzes data quality and coverage percentage for simulation viability
        # Returns comprehensive validation result with coverage analysis
        query = """
            SELECT 
                MIN(time) as earliest_date,
                MAX(time) as latest_date,
                COUNT(*) as record_count
            FROM stock_prices_daily 
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
        """
        try:
            results = await self.query_executor.execute_query(query, symbol.upper(), start_date, end_date)
            if not results or results[0]['record_count'] == 0:
                # Return structured result for no data case
                return {
                    'has_data': False,
                    'record_count': 0,
                    'earliest_date': None,
                    'latest_date': None,
                    'missing_days': (end_date - start_date).days + 1
                }
            
            result = results[0]
            expected_days = (end_date - start_date).days + 1
            actual_days = result['record_count']
            coverage_pct = (actual_days / expected_days) * 100 if expected_days > 0 else 0
            
            # Return comprehensive data quality analysis
            return {
                'has_data': True,
                'record_count': actual_days,
                'earliest_date': result['earliest_date'],
                'latest_date': result['latest_date'],
                'expected_days': expected_days,
                'coverage_percentage': coverage_pct,
                'sufficient_data': coverage_pct >= 50  # At least 50% coverage for meaningful backtest
            }
        except Exception as e:
            logger.error(f"Error validating date range for {symbol}: {e}")
            return {
                'has_data': False,
                'error': str(e)
            }
    
    async def validate_stock_tradeable(self, symbol: str, check_date: date) -> bool:
        # Validate if a stock was tradeable on a specific date using database function
        # Checks against IPO dates, delisting dates, and trading sessions
        # Returns boolean indicating trading eligibility
        query = "SELECT is_stock_tradeable($1, $2) as is_tradeable"
        
        try:
            results = await self.query_executor.execute_query(query, symbol.upper(), check_date)
            if results:
                return results[0]['is_tradeable']
            return False
        except Exception as e:
            logger.error(f"Error checking if {symbol} was tradeable on {check_date}: {e}")
            # Return False on error to prevent invalid trading
            return False
    
    async def get_eligible_stocks_for_period(self, start_date: date, end_date: date) -> List[str]:
        # Get list of stocks that were eligible for trading during the entire specified period
        # Uses database function to filter out stocks with IPO/delisting issues
        # Returns alphabetically sorted list of eligible stock symbols
        query = "SELECT symbol FROM get_eligible_stocks_for_period($1, $2) ORDER BY symbol"
        
        try:
            results = await self.query_executor.execute_query(query, start_date, end_date)
            return [row['symbol'] for row in results]
        except Exception as e:
            logger.error(f"Error getting eligible stocks for period {start_date} to {end_date}: {e}")
            # Return empty list on error to prevent invalid symbol usage
            return []
    
    async def get_stock_temporal_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Get comprehensive temporal information for a stock including IPO and delisting dates
        # Provides complete trading history metadata for temporal validation
        # Returns dictionary with temporal data or None if stock not found
        query = """
            SELECT symbol, ipo_date, listing_date, delisting_date,
                   trading_status, exchange_status, first_trading_date, last_trading_date
            FROM stocks 
            WHERE symbol = $1
        """
        
        try:
            results = await self.query_executor.execute_query(query, symbol.upper())
            if results:
                result = results[0]
                # Convert date objects to ISO format strings for JSON serialization
                for date_field in ['ipo_date', 'listing_date', 'delisting_date', 'first_trading_date', 'last_trading_date']:
                    if result[date_field]:
                        result[date_field] = result[date_field].isoformat()
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting temporal info for {symbol}: {e}")
            return None
    
    async def validate_symbols_for_period(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        # Comprehensive validation of multiple symbols for a specific trading period
        # Validates symbol existence, IPO dates, and delisting dates for simulation eligibility
        # Returns detailed validation results with categorized symbols and error messages
        if not symbols:
            return {"valid_symbols": [], "rejected_symbols": [], "errors": []}
        
        # Initialize validation result tracking
        valid_symbols = []
        rejected_symbols = []
        validation_errors = []
        
        # Iterate through each symbol for comprehensive validation
        for symbol in symbols:
            symbol_upper = symbol.upper()
            
            # First check: Symbol existence in database
            if not await self.validate_symbol_exists(symbol_upper):
                rejected_symbols.append(symbol_upper)
                validation_errors.append(f"Symbol {symbol_upper} not found in database")
                continue
            
            # Second check: IPO validation - was stock tradeable at start date
            start_tradeable = await self.validate_stock_tradeable(symbol_upper, start_date)
            if not start_tradeable:
                # Get detailed temporal info for comprehensive error messaging
                temporal_info = await self.get_stock_temporal_info(symbol_upper)
                error_msg = f"Stock {symbol_upper} was not tradeable on {start_date}"
                
                if temporal_info:
                    ipo_date = temporal_info.get('ipo_date')
                    listing_date = temporal_info.get('listing_date')
                    if ipo_date:
                        error_msg += f" (IPO date: {ipo_date})"
                    elif listing_date:
                        error_msg += f" (Listing date: {listing_date})"
                
                rejected_symbols.append(symbol_upper)
                validation_errors.append(error_msg)
                continue
            
            # Third check: Delisting validation - was stock still tradeable at end date
            end_tradeable = await self.validate_stock_tradeable(symbol_upper, end_date)
            if not end_tradeable:
                # Get detailed temporal info for comprehensive error messaging
                temporal_info = await self.get_stock_temporal_info(symbol_upper)
                error_msg = f"Stock {symbol_upper} was not tradeable on {end_date}"
                
                if temporal_info:
                    delisting_date = temporal_info.get('delisting_date')
                    if delisting_date:
                        error_msg += f" (Delisted on: {delisting_date})"
                
                rejected_symbols.append(symbol_upper)
                validation_errors.append(error_msg)
                continue
            
            # All validation checks passed - symbol is valid for the period
            valid_symbols.append(symbol_upper)
        
        # Return comprehensive validation results with statistics
        return {
            "valid_symbols": valid_symbols,
            "rejected_symbols": rejected_symbols,
            "errors": validation_errors,
            "total_requested": len(symbols),
            "total_valid": len(valid_symbols),
            "total_rejected": len(rejected_symbols)
        }
    
