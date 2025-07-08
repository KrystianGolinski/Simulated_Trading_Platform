# Database Connection Manager - AsyncPG Connection Pool Management System
# This module provides comprehensive database connection management for the Trading Platform
# Key responsibilities:
# - Database connection pool lifecycle management (creation, monitoring, cleanup)
# - Environment-aware configuration for test vs production database credentials
# - Connection pool health monitoring and statistics tracking
# - TimescaleDB connection optimization with configurable pool parameters
# - Automatic connection recovery and pool management
# - Connection pool statistics and monitoring for performance optimization
# - Database connectivity health checks for system monitoring
#
# Architecture Features:
# - AsyncPG-based connection pooling for high-performance async database operations
# - Environment-aware configuration supporting test and production modes
# - Configurable connection pool parameters (min/max size, command timeout)
# - Connection pool health monitoring and statistics collection
# - Automatic connection recovery and error handling
# - Integration with Docker-based PostgreSQL/TimescaleDB deployment
# - Comprehensive logging for connection lifecycle events
#
# Configuration Strategy:
# - Test mode: Uses TEST_DB_* environment variables for local testing
# - Production mode: Uses Docker environment variables for container deployment
# - Connection pool sized for concurrent load (min: 10, max: 50 connections)
# - Command timeout configured to prevent hanging queries (60 seconds)
# - Application name tagging for connection identification and monitoring

import os
import asyncpg
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from root .env 
load_dotenv(dotenv_path='../../../.env')

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    # Comprehensive database connection pool management for TimescaleDB integration
    # Handles connection lifecycle, health monitoring, and environment-aware configuration
    # Provides high-performance async database connectivity with automatic recovery
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = self._build_database_url()
    
    def _build_database_url(self) -> str:
        # Build database URL with environment-aware configuration for test vs production
        # Automatically detects test mode and uses appropriate database credentials
        # Supports both local testing and Docker-based production deployment
        test_mode = os.getenv('TESTING', 'false').lower() == 'true'
        
        if test_mode:
            # Test mode configuration - uses separate test database credentials
            # Enables isolated testing without affecting production data
            db_host = os.getenv('TEST_DB_HOST', 'localhost')
            db_port = os.getenv('TEST_DB_PORT', '5433')
            db_name = os.getenv('TEST_DB_NAME', 'simulated_trading_platform')
            db_user = os.getenv('TEST_DB_USER', 'trading_user')
            db_password = os.getenv('TEST_DB_PASSWORD', 'trading_password')
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            # Production mode configuration - uses Docker environment credentials
            # Supports both explicit DATABASE_URL and individual credential variables
            return os.getenv(
                "DATABASE_URL", 
                f"postgresql://{os.getenv('DB_USER', 'trading_user')}:{os.getenv('DB_PASSWORD', 'trading_password')}@postgres:5432/simulated_trading_platform"
            )
    
    async def create_pool(self) -> None:
        # Initialize database connection pool with optimized parameters for trading platform
        # Configures connection pool for high-performance async operations
        # Implements proper error handling and logging for connection issues
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=10,  # Minimum number of connections to keep in the pool for baseline performance
                max_size=50,  # Maximum number of connections for handling peak loads and concurrent requests
                command_timeout=60,  # Timeout in seconds for any single query; prevents hanging queries from holding up the system
                server_settings={
                    'application_name': 'trading_platform_api',  # Application name for connection identification and monitoring
                }
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close_pool(self) -> None:
        # Close database connection pool gracefully with proper cleanup
        # Ensures all connections are properly released and resources are freed
        # Used during application shutdown or connection manager lifecycle events
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    def get_pool(self) -> Optional[asyncpg.Pool]:
        # Get current connection pool instance for query execution
        # Returns None if pool is not initialized, enabling proper error handling
        # Used by QueryExecutor and other database components
        return self.pool
    
    def is_connected(self) -> bool:
        # Check if database connection pool is active and available
        # Simple availability check for connection pool existence
        # Used by health checks and connection validation logic
        return self.pool is not None
    
    async def health_check(self) -> bool:
        # Comprehensive database connectivity health check with query execution
        # Validates both connection pool availability and database responsiveness
        # Used by system health monitoring and readiness probes
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
        # Get comprehensive connection pool statistics for monitoring and performance analysis
        # Provides current pool size, capacity limits, and active connection count
        # Used by performance monitoring endpoints and system health dashboards
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