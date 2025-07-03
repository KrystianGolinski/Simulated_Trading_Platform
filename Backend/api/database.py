import os
import asyncpg
from typing import Optional, List, Dict, Any, Tuple
import logging
from datetime import datetime, date
import json
from dotenv import load_dotenv
import asyncio
from functools import lru_cache
import hashlib
from cachetools import TTLCache

# Load environment variables from root .env file
load_dotenv(dotenv_path='../../.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        # Determine if we're in test mode and use appropriate credentials
        test_mode = os.getenv('TESTING', 'false').lower() == 'true'
        
        if test_mode:
            # Use test database credentials for local testing
            db_host = os.getenv('TEST_DB_HOST', 'localhost')
            db_port = os.getenv('TEST_DB_PORT', '5433')
            db_name = os.getenv('TEST_DB_NAME', 'simulated_trading_platform')
            db_user = os.getenv('TEST_DB_USER', 'trading_user')
            db_password = os.getenv('TEST_DB_PASSWORD', 'trading_password')
            self.database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            # Not testing - use Docker environment credentials
            self.database_url = os.getenv(
                "DATABASE_URL", 
                f"postgresql://{os.getenv('DB_USER', 'trading_user')}:{os.getenv('DB_PASSWORD', 'trading_password')}@postgres:5432/simulated_trading_platform"
            )
        # Initialize cachetools caches
        self._stock_data_cache = TTLCache(maxsize=1024, ttl=300)  # 5 minutes TTL, max 1024 entries
        self._stocks_list_cache = TTLCache(maxsize=1, ttl=300)    # Cache for available stocks list
        self._validation_cache = TTLCache(maxsize=256, ttl=600)   # 10 minutes for validation results
    
    async def connect(self):
        # Initialize database connection pool
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=10,  # Min size of DB connections
                max_size=50,  # Max size of DB connections for performace
                command_timeout=60,  # Timeout for long queries (If not done by 60s usually signifies something has gone wrong)
                server_settings={
                    'application_name': 'trading_platform_api',
                }
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self):
        # Close database connection pool
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    
    async def clear_cache(self) -> None:
        # Clear all cached data
        self._stock_data_cache.clear()
        self._stocks_list_cache.clear()
        self._validation_cache.clear()
        logger.info("Database cache cleared")

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        # Execute a SELECT query and return results as list of dicts
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute_command(self, query: str, *args) -> str:
        # Execute INSERT/UPDATE/DELETE command
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args)
            return result

    async def get_available_stocks(self, page: int = 1, page_size: int = 100) -> Tuple[List[str], int]:
        # Get list of available stock symbols - returns (data, total_count)
        cache_key = f'available_stocks_{page}_{page_size}'
        
        # Check cache first
        if cache_key in self._stocks_list_cache:
            logger.debug(f"Cache hit for available stocks page {page}")
            cached_result = self._stocks_list_cache[cache_key]
            return cached_result['data'], cached_result['total_count']
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_query = "SELECT COUNT(DISTINCT symbol) as total FROM stock_prices_daily"
        count_result = await self.execute_query(count_query)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get results with pagination
        query = """
            SELECT DISTINCT symbol 
            FROM stock_prices_daily 
            ORDER BY symbol
            LIMIT $1 OFFSET $2
        """
        results = await self.execute_query(query, page_size, offset)
        stocks = [row['symbol'] for row in results]
        
        # Cache the results
        cache_data = {'data': stocks, 'total_count': total_count}
        self._stocks_list_cache[cache_key] = cache_data
        total_pages = (total_count + page_size - 1) // page_size
        logger.debug(f"Fetched and cached {len(stocks)} available stocks (page {page}/{total_pages})")
        
        return stocks, total_count
    

    async def get_stock_data_batch(self, symbols: List[str], start_date: date, end_date: date, timeframe: str = 'daily') -> Dict[str, List[Dict[str, Any]]]:
        # Get historical stock data for multiple symbols
        if not symbols:
            return {}
        
        # Create placeholders for IN clause
        placeholders = ','.join(f'${i+1}' for i in range(len(symbols)))
        
        table_name = 'stock_prices_daily'
        
        query = f"""
            SELECT symbol, time, open, high, low, close, volume 
            FROM {table_name}
            WHERE symbol IN ({placeholders})
            AND time BETWEEN ${len(symbols)+1} AND ${len(symbols)+2}
            ORDER BY symbol, time
        """
        
        try:
            results = await self.execute_query(query, *[s.upper() for s in symbols], start_date, end_date)
            
            # Group results by symbol
            symbol_data = {}
            for row in results:
                symbol = row['symbol']
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                symbol_data[symbol].append(row)
            
            # Ensure all requested symbols are represented
            for symbol in symbols:
                if symbol.upper() not in symbol_data:
                    symbol_data[symbol.upper()] = []
            
            return symbol_data
            
        except Exception as e:
            logger.error(f"Error fetching batch stock data for {symbols}: {e}")
            return {symbol.upper(): [] for symbol in symbols}

    async def get_stock_data(self, symbol: str, start_date: date, end_date: date, timeframe: str = 'daily', 
                           page: int = 1, page_size: int = 1000) -> Tuple[List[Dict[str, Any]], int, Dict[str, str]]:
        # Get historical stock data - returns (data, total_count, date_range)
        cache_key = f"{symbol}_{start_date}_{end_date}_{timeframe}_{page}_{page_size}"
        
        # Check cache first
        if cache_key in self._stock_data_cache:
            logger.debug(f"Cache hit for stock data: {symbol} {start_date} to {end_date} page {page}")
            cached_result = self._stock_data_cache[cache_key]
            return cached_result['data'], cached_result['total_count'], cached_result['date_range']
        
        if timeframe == 'daily':
            table = 'stock_prices_daily'
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count for this symbol and date range
        count_query = f"""
            SELECT COUNT(*) as total
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
        """
        count_result = await self.execute_query(count_query, symbol, start_date, end_date)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get results with pagination
        query = f"""
            SELECT time, symbol, open, high, low, close, volume
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
            ORDER BY time ASC
            LIMIT $4 OFFSET $5
        """
        
        data = await self.execute_query(query, symbol, start_date, end_date, page_size, offset)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Cache the results
        cache_data = {
            'data': data,
            'total_count': total_count,
            'date_range': date_range
        }
        self._stock_data_cache[cache_key] = cache_data
        total_pages = (total_count + page_size - 1) // page_size
        logger.debug(f"Fetched and cached stock data: {symbol} {start_date} to {end_date} page {page}/{total_pages} ({len(data)} records)")
        
        return data, total_count, date_range
    

    async def create_trading_session(self, user_id: str, strategy_name: str,
                                   initial_capital: float, start_date: date,
                                   end_date: date, symbols: List[str],
                                   parameters: Dict[str, Any]) -> int:
        # Create a new trading session and return session ID
        
        query = """
            INSERT INTO trading_sessions 
            (start_date, end_date, initial_capital, strategy_name, strategy_params)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            session_id = await conn.fetchval(
                query, start_date, end_date, initial_capital, 
                strategy_name, json.dumps(parameters)
            )
            return session_id

    async def log_trade(self, session_id: int, symbol: str, action: str,
                       quantity: int, price: float, timestamp: datetime,
                       commission: float = 0.0) -> int:
        # Log a trade execution
        
        query = """
            INSERT INTO trades_log 
            (session_id, symbol, trade_time, action, quantity, price, commission)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            trade_id = await conn.fetchval(
                query, session_id, symbol, timestamp, action, 
                quantity, price, commission
            )
            return trade_id

    async def get_session_trades(self, session_id: int, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        # Get trades for a session
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM trades_log 
            WHERE session_id = $1
        """
        count_result = await self.execute_query(count_query, session_id)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get results with pagination
        query = """
            SELECT symbol, action, quantity, price, commission, trade_time
            FROM trades_log 
            WHERE session_id = $1
            ORDER BY trade_time ASC
            LIMIT $2 OFFSET $3
        """
        
        trades = await self.execute_query(query, session_id, page_size, offset)
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return {
            'data': trades,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous
            },
            'session_id': session_id
        }
    

    async def get_session_results(self, session_id: int) -> Optional[Dict[str, Any]]:
        # Get session results
        
        query = """
            SELECT id, start_date, end_date, initial_capital, 
                   strategy_name, strategy_params, created_at
            FROM trading_sessions 
            WHERE id = $1
        """
        
        results = await self.execute_query(query, session_id)
        if not results:
            return None
        
        session = results[0]
        
        # Get trades for this session (first page only for session results)
        trades_result = await self.get_session_trades(session_id, page=1, page_size=1000)
        session['trades'] = trades_result
        
        return session

    async def validate_symbol_exists(self, symbol: str) -> bool:
        # Check if a stock symbol exists in the database
        cache_key = f"symbol_exists_{symbol.upper()}"
        
        # Check cache first
        if cache_key in self._validation_cache:
            logger.debug(f"Cache hit for symbol validation: {symbol}")
            return self._validation_cache[cache_key]
        
        query = """
            SELECT COUNT(*) as count
            FROM stock_prices_daily 
            WHERE symbol = $1
        """
        try:
            results = await self.execute_query(query, symbol.upper())
            exists = results[0]['count'] > 0 if results else False
            
            # Cache the result
            self._validation_cache[cache_key] = exists
            logger.debug(f"Validated and cached symbol existence: {symbol} = {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking symbol {symbol}: {e}")
            return False
    
    async def validate_date_range_has_data(self, symbol: str, start_date: date, end_date: date) -> Dict[str, Any]:
        # Check if data exists for symbol in the specified date range
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
            results = await self.execute_query(query, symbol.upper(), start_date, end_date)
            if not results or results[0]['record_count'] == 0:
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
    
    async def get_symbol_date_range(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Get the available date range for a symbol
        cache_key = f"date_range_{symbol.upper()}"
        
        # Check cache first
        if cache_key in self._validation_cache:
            logger.debug(f"Cache hit for date range: {symbol}")
            return self._validation_cache[cache_key]
        
        query = """
            SELECT 
                MIN(time) as earliest_date,
                MAX(time) as latest_date,
                COUNT(*) as total_records
            FROM stock_prices_daily 
            WHERE symbol = $1
        """
        try:
            results = await self.execute_query(query, symbol.upper())
            result = results[0] if results and results[0]['total_records'] > 0 else None
            
            # Cache the result
            self._validation_cache[cache_key] = result
            logger.debug(f"Fetched and cached date range for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Error getting date range for {symbol}: {e}")
            return None
    
    async def validate_multiple_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        # Validate multiple symbols at once
        if not symbols:
            return {}
        
        # Create placeholders for IN clause
        placeholders = ','.join(f'${i+1}' for i in range(len(symbols)))
        query = f"""
            SELECT DISTINCT symbol
            FROM stock_prices_daily 
            WHERE symbol IN ({placeholders})
        """
        
        try:
            results = await self.execute_query(query, *[s.upper() for s in symbols])
            existing_symbols = {row['symbol'] for row in results}
            
            return {symbol.upper(): symbol.upper() in existing_symbols for symbol in symbols}
        except Exception as e:
            logger.error(f"Error validating symbols {symbols}: {e}")
            return {symbol.upper(): False for symbol in symbols}
    
    # Temporal validation methods
    async def validate_stock_tradeable(self, symbol: str, check_date: date) -> bool:
        # Check if a stock was tradeable on a specific date using database function
        query = "SELECT is_stock_tradeable($1, $2) as is_tradeable"
        
        try:
            results = await self.execute_query(query, symbol.upper(), check_date)
            if results:
                return results[0]['is_tradeable']
            return False
        except Exception as e:
            logger.error(f"Error checking if {symbol} was tradeable on {check_date}: {e}")
            return False
    
    async def get_eligible_stocks_for_period(self, start_date: date, end_date: date) -> List[str]:
        # Get stocks that were eligible for trading during a specific period
        query = "SELECT symbol FROM get_eligible_stocks_for_period($1, $2) ORDER BY symbol"
        
        try:
            results = await self.execute_query(query, start_date, end_date)
            return [row['symbol'] for row in results]
        except Exception as e:
            logger.error(f"Error getting eligible stocks for period {start_date} to {end_date}: {e}")
            return []
    
    async def get_stock_temporal_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Get temporal information for a stock
        query = """
            SELECT symbol, ipo_date, listing_date, delisting_date,
                   trading_status, exchange_status, first_trading_date, last_trading_date
            FROM stocks 
            WHERE symbol = $1
        """
        
        try:
            results = await self.execute_query(query, symbol.upper())
            if results:
                result = results[0]
                # Convert dates to strings for JSON serialization
                for date_field in ['ipo_date', 'listing_date', 'delisting_date', 'first_trading_date', 'last_trading_date']:
                    if result[date_field]:
                        result[date_field] = result[date_field].isoformat()
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting temporal info for {symbol}: {e}")
            return None
    
    async def validate_symbols_for_period(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        # Validate multiple symbols for a specific period
        if not symbols:
            return {"valid_symbols": [], "rejected_symbols": [], "errors": []}
        
        valid_symbols = []
        rejected_symbols = []
        validation_errors = []
        
        for symbol in symbols:
            symbol_upper = symbol.upper()
            
            # Check if symbol exists in database
            if not await self.validate_symbol_exists(symbol_upper):
                rejected_symbols.append(symbol_upper)
                validation_errors.append(f"Symbol {symbol_upper} not found in database")
                continue
            
            # Check if stock was tradeable at start date (IPO validation)
            start_tradeable = await self.validate_stock_tradeable(symbol_upper, start_date)
            if not start_tradeable:
                # Get temporal info for detailed error
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
            
            # Check if stock was still tradeable at end date (delisting validation)
            end_tradeable = await self.validate_stock_tradeable(symbol_upper, end_date)
            if not end_tradeable:
                # Get temporal info for detailed error
                temporal_info = await self.get_stock_temporal_info(symbol_upper)
                error_msg = f"Stock {symbol_upper} was not tradeable on {end_date}"
                
                if temporal_info:
                    delisting_date = temporal_info.get('delisting_date')
                    if delisting_date:
                        error_msg += f" (Delisted on: {delisting_date})"
                
                rejected_symbols.append(symbol_upper)
                validation_errors.append(error_msg)
                continue
            
            # Validation passed, valid symbol
            valid_symbols.append(symbol_upper)
        
        return {
            "valid_symbols": valid_symbols,
            "rejected_symbols": rejected_symbols,
            "errors": validation_errors,
            "total_requested": len(symbols),
            "total_valid": len(valid_symbols),
            "total_rejected": len(rejected_symbols)
        }
    
    async def validate_simulation_temporal(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        # Simulation validation
        validation_result = await self.validate_symbols_for_period(symbols, start_date, end_date)
        
        if validation_result["total_valid"] == 0:
            return {
                **validation_result,
                "simulation_valid": False,
                "simulation_error": "No valid symbols for the specified period"
            }
        
        # Check if we lost too many symbols (more than 50% rejected might indicate issue)
        rejection_rate = validation_result["total_rejected"] / validation_result["total_requested"]
        if rejection_rate > 0.5:
            logger.warning(f"High symbol rejection rate: {rejection_rate:.1%} for period {start_date} to {end_date}")
        
        return {
            **validation_result,
            "simulation_valid": True,
            "rejection_rate": rejection_rate,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        # Get database performance statistics
        if not self.pool:
            return {"error": "Database not connected"}
        
        try:
            # Get connection pool stats
            pool_stats = {
                "size": self.pool.get_size() if hasattr(self.pool, 'get_size') else 0,
                "min_size": self.pool.get_min_size() if hasattr(self.pool, 'get_min_size') else 0,
                "max_size": self.pool.get_max_size() if hasattr(self.pool, 'get_max_size') else 0,
            }
            
            # Get cache stats
            cache_stats = {
                "stock_data_cache_size": len(self._stock_data_cache),
                "stock_data_cache_maxsize": self._stock_data_cache.maxsize,
                "stocks_list_cache_size": len(self._stocks_list_cache),
                "validation_cache_size": len(self._validation_cache),
                "validation_cache_maxsize": self._validation_cache.maxsize,
            }
            
            return {
                "pool_stats": pool_stats,
                "cache_stats": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        # Health check with performance metrics
        if not self.pool:
            return {"status": "disconnected"}
        
        try:
            # Test basic query
            result = await self.execute_query("SELECT NOW() as current_time")
            current_time = result[0]['current_time']
            
            # Get data stats
            stats_query = """
                SELECT 
                    (SELECT COUNT(DISTINCT symbol) FROM stock_prices_daily) as symbols_daily,
                    (SELECT COUNT(*) FROM stock_prices_daily) as daily_records,
                    (SELECT COUNT(*) FROM trading_sessions) as total_sessions,
                    (SELECT COUNT(*) FROM trades_log) as total_trades
            """
            
            stats = await self.execute_query(stats_query)
            
            # Get performance stats
            perf_stats = await self.get_performance_stats()
            
            return {
                "status": "healthy",
                "database": "simulated_trading_platform",
                "current_time": current_time,
                "connection_pool_size": len(self.pool._holders) if self.pool._holders else 0,
                "data_stats": stats[0] if stats else {},
                "performance_stats": perf_stats
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    # Dependency injection for FastAPI
    if not db_manager.pool:
        await db_manager.connect()
    return db_manager