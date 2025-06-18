import os
import asyncpg
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date
import json
from dotenv import load_dotenv
import asyncio
from functools import lru_cache
import hashlib

# Load environment variables from root .env file
load_dotenv(dotenv_path='../../.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        # Get credentials from environment
        self.database_url = os.getenv(
            "DATABASE_URL", 
            f"postgresql://{os.getenv('DB_USER', 'trading_user')}:{os.getenv('DB_PASSWORD', 'trading_password')}@localhost:5433/simulated_trading_platform"
        )
        # Add caching for frequently accessed data
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes TTL
        self._available_stocks_cache: Optional[List[str]] = None
        self._available_stocks_cache_time: Optional[datetime] = None
    
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
    
    def _get_cache_key(self, *args) -> str:
        # Generate cache key from arguments using md5
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        # Check if cache entry is still valid
        if cache_key not in self._cache_timestamps:
            return False
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self._cache_ttl
    
    def _set_cache(self, cache_key: str, value: Any) -> None:
        # Set cache value with timestamp
        self._cache[cache_key] = value
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        # Get cache value if valid
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None
    
    async def clear_cache(self) -> None:
        # Clear all cached data
        self._cache.clear()
        self._cache_timestamps.clear()
        self._available_stocks_cache = None
        self._available_stocks_cache_time = None
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

    async def get_available_stocks(self) -> List[str]:
        # Get list of available stock symbols with caching
        
        # Check cache first
        if (self._available_stocks_cache and self._available_stocks_cache_time and 
            (datetime.now() - self._available_stocks_cache_time).total_seconds() < self._cache_ttl):
            return self._available_stocks_cache
        
        # Query database
        query = """
            SELECT DISTINCT symbol 
            FROM stock_prices_daily 
            ORDER BY symbol
        """
        results = await self.execute_query(query)
        stocks = [row['symbol'] for row in results]
        
        # Cache the results
        self._available_stocks_cache = stocks
        self._available_stocks_cache_time = datetime.now()
        logger.debug(f"Cached {len(stocks)} available stocks")
        
        return stocks

    async def get_stock_data(self, symbol: str, start_date: date, end_date: date, timeframe: str = 'daily') -> List[Dict[str, Any]]:
        # Get historical stock data with caching
        
        # Check cache first
        cache_key = self._get_cache_key("stock_data", symbol, start_date, end_date, timeframe)
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for stock data: {symbol} {start_date} to {end_date}")
            return cached_data
        
        if timeframe == 'daily':
            table = 'stock_prices_daily'
        elif timeframe == '1min':
            table = 'stock_prices_1min'
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Optimized query with index hints
        query = f"""
            SELECT time, symbol, open, high, low, close, volume
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
            ORDER BY time ASC
        """
        
        data = await self.execute_query(query, symbol, start_date, end_date)
        
        # Cache the results
        self._set_cache(cache_key, data)
        logger.debug(f"Cached stock data: {symbol} {start_date} to {end_date} ({len(data)} records)")
        
        return data

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

    async def get_session_trades(self, session_id: int) -> List[Dict[str, Any]]:
        # Get all trades for a session
        
        query = """
            SELECT symbol, action, quantity, price, commission, trade_time
            FROM trades_log 
            WHERE session_id = $1
            ORDER BY trade_time ASC
        """
        
        return await self.execute_query(query, session_id)

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
        
        # Get trades for this session
        trades = await self.get_session_trades(session_id)
        session['trades'] = trades
        
        return session

    async def validate_symbol_exists(self, symbol: str) -> bool:
        # Check if a stock symbol exists in the database
        query = """
            SELECT COUNT(*) as count
            FROM stock_prices_daily 
            WHERE symbol = $1
        """
        try:
            results = await self.execute_query(query, symbol.upper())
            return results[0]['count'] > 0 if results else False
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
            return results[0] if results and results[0]['total_records'] > 0 else None
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
                "cache_entries": len(self._cache),
                "cache_hit_potential": len([k for k in self._cache.keys() if self._is_cache_valid(k)]),
                "available_stocks_cached": self._available_stocks_cache is not None,
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
        # Enhanced health check with performance metrics
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
                    (SELECT COUNT(*) FROM stock_prices_1min) as intraday_records,
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