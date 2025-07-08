# Database Configuration and Management Layer
# This file provides the main database interface for the Trading Platform API
# It coordinates between low-level database components and high-level business logic
# Key responsibilities:
# - Database connection lifecycle management
# - Trading session and trade logging
# - Health monitoring and performance statistics
# - Dependency injection for FastAPI endpoints

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date
import json

# Database component imports - following layered architecture
from db_components.connection_manager import DatabaseConnectionManager
from db_components.query_executor import QueryExecutor
from db_components.cache_manager import CacheManager
from repositories.stock_data_repository import StockDataRepository

logger = logging.getLogger(__name__)

class DatabaseManager:
    # Central database manager that coordinates all database operations
    # Uses composition to integrate specialized database components
    # Follows single responsibility principle with dedicated components for:
    # - Connection management (pool creation, health monitoring)
    # - Query execution (parameterized queries, transaction handling)
    # - Caching (in-memory caching for frequently accessed data)
    # - Stock data access (repository pattern for stock-related operations)
    
    def __init__(self):
        # Compose services following single responsibility principle
        # Each component handles a specific aspect of database operations
        self.connection_manager = DatabaseConnectionManager()  # Handles connection pooling
        self.query_executor = QueryExecutor(self.connection_manager)  # Executes queries safely
        self.cache_manager = CacheManager()  # Manages in-memory caching
        self.stock_data_repository = StockDataRepository(self.query_executor, self.cache_manager)  # Stock data access
    
    async def connect(self):
        # Initialize database connection pool
        # Called during application startup to establish connection pool
        await self.connection_manager.create_pool()
    
    async def disconnect(self):
        # Close database connection pool and clean up resources
        # Called during application shutdown to ensure graceful cleanup
        await self.connection_manager.close_pool()
    
    # Trading session methods using query executor
    # These methods handle simulation metadata and results storage
    
    async def create_trading_session(self, user_id: str, strategy_name: str,
                                   initial_capital: float, start_date: date,
                                   end_date: date, symbols: List[str],
                                   parameters: Dict[str, Any]) -> int:
        # Create a new trading session record in the database
        # Returns the session ID for tracking simulation progress and results
        # Used by simulation engine to persist simulation metadata
        query = """
            INSERT INTO trading_sessions 
            (start_date, end_date, initial_capital, strategy_name, strategy_params)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        # Execute query and return the generated session ID
        session_id = await self.query_executor.execute_fetchval(
            query, start_date, end_date, initial_capital, 
            strategy_name, json.dumps(parameters)
        )
        return session_id
    
    async def log_trade(self, session_id: int, symbol: str, action: str,
                       quantity: int, price: float, timestamp: datetime,
                       commission: float = 0.0) -> int:
        # Log individual trade execution to the database
        # Each trade record includes all execution details for performance analysis
        # Used by simulation engine to record trade history
        query = """
            INSERT INTO trades_log 
            (session_id, symbol, trade_time, action, quantity, price, commission)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        # Execute query and return the generated trade ID
        trade_id = await self.query_executor.execute_fetchval(
            query, session_id, symbol, timestamp, action, 
            quantity, price, commission
        )
        return trade_id
    
    async def get_session_trades(self, session_id: int, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        # Retrieve paginated trade records for a specific trading session
        # Returns trade data with pagination metadata for frontend display
        # Used by simulation results endpoints to show trade history
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get total count for pagination metadata
        count_query = """
            SELECT COUNT(*) as total
            FROM trades_log 
            WHERE session_id = $1
        """
        count_result = await self.query_executor.execute_query(count_query, session_id)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get paginated trade records ordered by execution time
        query = """
            SELECT symbol, action, quantity, price, commission, trade_time
            FROM trades_log 
            WHERE session_id = $1
            ORDER BY trade_time ASC
            LIMIT $2 OFFSET $3
        """
        
        trades = await self.query_executor.execute_query(query, session_id, page_size, offset)
        
        # Calculate pagination metadata for frontend pagination controls
        # Use integer division to calculate total pages, ensuring the last page is counted.
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
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
        # Retrieve complete session results including metadata and trade history
        # Returns all session data needed for simulation results display
        # Used by simulation results endpoints to provide comprehensive session information
        query = """
            SELECT id, start_date, end_date, initial_capital, 
                   strategy_name, strategy_params, created_at
            FROM trading_sessions 
            WHERE id = $1
        """
        
        results = await self.query_executor.execute_query(query, session_id)
        if not results:
            return None
        
        session = results[0]
        
        # Get trades for this session (first page only for session results)
        # Limited to 1000 trades to prevent memory issues with large simulations
        trades_result = await self.get_session_trades(session_id, page=1, page_size=1000)
        session['trades'] = trades_result
        
        return session
    
    # Health and performance methods
    # These methods provide system monitoring and diagnostics for the database layer
    
    async def health_check(self) -> Dict[str, Any]:
        # Comprehensive database health check with performance metrics
        # Used by health endpoints to provide system status information
        # Includes connection status, data statistics, and performance metrics
        if not self.connection_manager.is_connected():
            return {"status": "disconnected"}
        
        try:
            # Test basic query using query executor to verify database connectivity
            result = await self.query_executor.execute_query("SELECT NOW() as current_time")
            current_time = result[0]['current_time']
            
            # Get comprehensive data statistics for system overview
            stats_query = """
                SELECT 
                    (SELECT COUNT(DISTINCT symbol) FROM stock_prices_daily) as symbols_daily,
                    (SELECT COUNT(*) FROM stock_prices_daily) as daily_records,
                    (SELECT COUNT(*) FROM trading_sessions) as total_sessions,
                    (SELECT COUNT(*) FROM trades_log) as total_trades
            """
            
            stats = await self.query_executor.execute_query(stats_query)
            
            # Get performance stats using our component architecture
            perf_stats = await self.get_performance_stats()
            
            return {
                "status": "healthy",
                "database": "simulated_trading_platform",
                "current_time": current_time,
                "connection_pool_size": self.connection_manager.get_pool_stats().get("connection_count", 0),
                "data_stats": stats[0] if stats else {},
                "performance_stats": perf_stats
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        # Retrieve comprehensive database performance statistics
        # Aggregates performance data from all database components
        # Used for monitoring, optimization, and troubleshooting
        if not self.connection_manager.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Get connection pool statistics from connection manager
            # Includes active connections, pool utilization, and connection health
            pool_stats = self.connection_manager.get_pool_stats()
            
            # Get cache performance statistics from cache manager
            # Includes hit rates, cache size, and memory usage
            cache_stats = self.cache_manager.get_cache_stats()
            
            return {
                "pool_stats": pool_stats,
                "cache_stats": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
# Global database manager instance with modularity
# Singleton pattern ensures consistent database state across the application
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    # Dependency injection function for FastAPI endpoints
    # Ensures database connection is established before use
    # Used by all routers to access database functionality
    if not db_manager.connection_manager.is_connected():
        await db_manager.connect()
    return db_manager