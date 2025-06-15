import os
import asyncpg
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date
import json
from dotenv import load_dotenv

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
    
    async def connect(self):
        # Initialize database connection pool
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
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
        # Get list of available stock symbols from price data
        query = """
            SELECT DISTINCT symbol 
            FROM stock_prices_daily 
            ORDER BY symbol
        """
        results = await self.execute_query(query)
        return [row['symbol'] for row in results]

    async def get_stock_data(self, symbol: str, start_date: date, end_date: date, timeframe: str = 'daily') -> List[Dict[str, Any]]:
        # Get historical stock data for backtesting
        
        if timeframe == 'daily':
            table = 'stock_prices_daily'
        elif timeframe == '1min':
            table = 'stock_prices_1min'
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        query = f"""
            SELECT time, symbol, open, high, low, close, volume
            FROM {table}
            WHERE symbol = $1 
            AND time >= $2 
            AND time <= $3
            ORDER BY time ASC
        """
        
        return await self.execute_query(query, symbol, start_date, end_date)

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

    async def health_check(self) -> Dict[str, Any]:
        # Check database health and return stats
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
            
            return {
                "status": "healthy",
                "database": "simulated_trading_platform",
                "current_time": current_time,
                "connection_pool_size": len(self.pool._holders) if self.pool._holders else 0,
                "data_stats": stats[0] if stats else {}
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