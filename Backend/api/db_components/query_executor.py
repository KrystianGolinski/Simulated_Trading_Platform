# Query Executor - Raw Database Query Execution with Retry Logic
# This module provides comprehensive query execution capabilities for the Trading Platform database operations
# Key responsibilities:
# - Raw SQL query execution with comprehensive error handling and retry logic
# - Transaction support for atomic multi-query operations
# - Batch query execution for bulk operations
# - Connection pool integration with timeout management
# - Exponential backoff retry strategy for concurrent access issues
# - Query result processing and type conversion
# - Comprehensive logging for query execution monitoring
#
# Architecture Features:
# - Retry logic with exponential backoff for handling concurrent access issues
# - Transaction support for atomicity in complex operations
# - Batch execution capabilities for bulk data operations
# - Connection timeout management to prevent resource exhaustion
# - Comprehensive error handling with detailed logging and context
# - Integration with DatabaseConnectionManager for connection pool management
# - Type-safe result processing with automatic dictionary conversion
#
# Query Types Supported:
# - SELECT queries with list of dictionaries result format
# - INSERT/UPDATE/DELETE commands with status result
# - Single value queries (fetchval) for aggregate operations
# - Transaction-wrapped multi-query operations
# - Batch execution for bulk operations with same query pattern
#
# Retry Strategy:
# - Maximum 3 retry attempts for concurrent access issues
# - Exponential backoff starting at 0.1 seconds
# - Specific handling for "operation is in progress" errors
# - Comprehensive logging for retry attempts and final failures

import asyncpg
import asyncio
from typing import List, Dict, Any, Optional
import logging
from db_components.connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)

class QueryExecutor:
    # Comprehensive database query execution with retry logic and transaction support
    # Handles all types of SQL operations with robust error handling and performance optimization
    # Integrates with connection pool for high-performance async database operations
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        # Execute SELECT query with retry logic and return results as list of dictionaries
        # Implements exponential backoff for concurrent access issues
        # Converts asyncpg Row objects to dictionaries for consistent API response format
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    rows = await conn.fetch(query, *args)
                    return [dict(row) for row in rows]
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff for concurrent access resolution
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying query after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Log appropriate error level based on error type
                    if "operation is in progress" in str(e):
                        logger.warning(f"Query failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Query execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_command(self, query: str, *args) -> str:
        # Execute INSERT/UPDATE/DELETE command with retry logic and return status result
        # Handles data modification operations with proper error handling
        # Returns command status string indicating number of affected rows
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    result = await conn.execute(query, *args)
                    return result
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff for concurrent access resolution
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying command after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Log appropriate error level based on error type
                    if "operation is in progress" in str(e):
                        logger.warning(f"Command failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Command execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_fetchval(self, query: str, *args) -> Any:
        # Execute query and return single value for aggregate operations and INSERT RETURNING
        # Used for COUNT queries, MAX/MIN operations, and retrieving generated IDs
        # Implements retry logic for reliable single value retrieval
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    result = await conn.fetchval(query, *args)
                    return result
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff for concurrent access resolution
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying fetchval after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Log appropriate error level based on error type
                    if "operation is in progress" in str(e):
                        logger.warning(f"Fetchval failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Fetchval execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        # Execute multiple queries in atomic transaction with automatic rollback on failure
        # Takes list of (query_string, *args) tuples for complex multi-step operations
        # Ensures data consistency through transaction atomicity
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        try:
            async with pool.acquire(timeout=10.0) as conn:
                async with conn.transaction():
                    for query_tuple in queries:
                        query = query_tuple[0]
                        args = query_tuple[1:] if len(query_tuple) > 1 else ()
                        await conn.execute(query, *args)
                    return True
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            raise
    
    async def execute_batch(self, query: str, args_list: List[tuple]) -> List[str]:
        # Execute same query with multiple parameter sets for bulk operations
        # Optimized for bulk INSERT/UPDATE operations with consistent query pattern
        # Returns list of execution results for each parameter set
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        try:
            async with pool.acquire(timeout=10.0) as conn:
                results = []
                for args in args_list:
                    result = await conn.execute(query, *args)
                    results.append(result)
                return results
        except Exception as e:
            logger.error(f"Batch execution failed: \n{query}\n - Error: {e}")
            raise