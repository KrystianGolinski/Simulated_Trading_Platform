import asyncpg
import asyncio
from typing import List, Dict, Any, Optional
import logging
from db_components.connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)

class QueryExecutor:
    # Handles raw query execution and result processing only
    # Single responsibility: Query execution
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        # Execute a SELECT query and return results as list of dicts
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    rows = await conn.fetch(query, *args)
                    return [dict(row) for row in rows]
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying query after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Only log error if all retries failed
                    if "operation is in progress" in str(e):
                        logger.warning(f"Query failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Query execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_command(self, query: str, *args) -> str:
        # Execute INSERT/UPDATE/DELETE command and return result status
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    result = await conn.execute(query, *args)
                    return result
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying command after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Only log error if all retries failed
                    if "operation is in progress" in str(e):
                        logger.warning(f"Command failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Command execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_fetchval(self, query: str, *args) -> Any:
        # Execute query and return single value (for INSERT RETURNING, etc.)
        pool = self.connection_manager.get_pool()
        if not pool:
            raise RuntimeError("Database not connected")
        
        # Retry logic for concurrent access issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with pool.acquire(timeout=10.0) as conn:
                    result = await conn.fetchval(query, *args)
                    return result
            except Exception as e:
                if "operation is in progress" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    logger.debug(f"Retrying fetchval after {wait_time}s due to concurrent access issue (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Only log error if all retries failed
                    if "operation is in progress" in str(e):
                        logger.warning(f"Fetchval failed after {max_retries} retries due to concurrent access: \n{query}\n with args {args}")
                    else:
                        logger.error(f"Fetchval execution failed: \n{query}\n with args {args} - Error: {e}")
                    raise
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        # Execute multiple queries in a transaction
        # queries: List of (query_string, *args) tuples
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
        # Execute same query with multiple parameter sets
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