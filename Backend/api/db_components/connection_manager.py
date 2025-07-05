import os
import asyncpg
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from root .env 
load_dotenv(dotenv_path='../../../.env')

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    # Manages database connection lifecycle and pooling only
    # Single responsibility: Connection management
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = self._build_database_url()
    
    def _build_database_url(self) -> str:
        # Build database URL based on environment
        # Determine if we're in test mode and use appropriate credentials
        test_mode = os.getenv('TESTING', 'false').lower() == 'true'
        
        if test_mode:
            # Use test database credentials for local testing
            db_host = os.getenv('TEST_DB_HOST', 'localhost')
            db_port = os.getenv('TEST_DB_PORT', '5433')
            db_name = os.getenv('TEST_DB_NAME', 'simulated_trading_platform')
            db_user = os.getenv('TEST_DB_USER', 'trading_user')
            db_password = os.getenv('TEST_DB_PASSWORD', 'trading_password')
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            # Not testing - use Docker environment credentials
            return os.getenv(
                "DATABASE_URL", 
                f"postgresql://{os.getenv('DB_USER', 'trading_user')}:{os.getenv('DB_PASSWORD', 'trading_password')}@postgres:5432/simulated_trading_platform"
            )
    
    async def create_pool(self) -> None:
        # Initialize database connection pool
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=10,  # Minimum number of connections to keep in the pool.
                max_size=50,  # Maximum number of connections for handling peak loads.
                command_timeout=60,  # Timeout in seconds for any single query; prevents hanging queries from holding up the system.
                server_settings={
                    'application_name': 'trading_platform_api',
                }
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close_pool(self) -> None:
        # Close database connection pool
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    def get_pool(self) -> Optional[asyncpg.Pool]:
        # Get current connection pool
        return self.pool
    
    def is_connected(self) -> bool:
        # Check if database is connected
        return self.pool is not None
    
    async def health_check(self) -> bool:
        # Basic connectivity health check
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database connection health check failed: {e}")
            return False
    
    def get_pool_stats(self) -> dict:
        # Get connection pool statistics
        if not self.pool:
            return {"error": "Database not connected"}
        
        try:
            return {
                "size": self.pool.get_size() if hasattr(self.pool, 'get_size') else 0,
                "min_size": self.pool.get_min_size() if hasattr(self.pool, 'get_min_size') else 0,
                "max_size": self.pool.get_max_size() if hasattr(self.pool, 'get_max_size') else 0,
                "connection_count": len(self.pool._holders) if hasattr(self.pool, '_holders') and self.pool._holders else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return {"error": str(e)}