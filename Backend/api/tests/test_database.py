import pytest
from unittest.mock import AsyncMock, patch
from database import DatabaseManager
import asyncpg

class TestDatabaseManager:
    
    def test_init(self):
        # Test DatabaseManager initialization
        db = DatabaseManager()
        assert db.pool is None
        assert db.database_url.startswith("postgresql://")
    
    @pytest.mark.asyncio
    @patch('database.asyncpg.create_pool')
    async def test_connect_success(self, mock_create_pool):
        # Test successful database connection
        mock_pool = AsyncMock()
        # Make the mock return an awaitable
        async def create_pool_side_effect(*args, **kwargs):
            return mock_pool
        mock_create_pool.side_effect = create_pool_side_effect
        
        db = DatabaseManager()
        await db.connect()
        
        assert db.pool == mock_pool
        mock_create_pool.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('database.asyncpg.create_pool')
    async def test_connect_failure(self, mock_create_pool):
        # Test database connection failure
        async def create_pool_side_effect(*args, **kwargs):
            raise Exception("Connection failed")
        mock_create_pool.side_effect = create_pool_side_effect
        
        db = DatabaseManager()
        
        with pytest.raises(Exception, match="Connection failed"):
            await db.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_with_pool(self):
        # Test disconnection when pool exists
        db = DatabaseManager()
        mock_pool = AsyncMock()
        db.pool = mock_pool
        
        await db.disconnect()
        
        mock_pool.close.assert_called_once()
        assert db.pool is None
    
    @pytest.mark.asyncio
    async def test_disconnect_without_pool(self):
        # Test disconnection when no pool exists
        db = DatabaseManager()
        db.pool = None
        
        # Should not raise exception
        await db.disconnect()
        assert db.pool is None
    
    @pytest.mark.asyncio
    async def test_ensure_connected_already_connected(self):
        # Test ensure_connected when already connected
        db = DatabaseManager()
        mock_pool = AsyncMock()
        db.pool = mock_pool
        
        await db._ensure_connected()
        
        # Should not try to reconnect
        assert db.pool == mock_pool
    
    @pytest.mark.asyncio
    @patch('database.DatabaseManager.connect')
    async def test_ensure_connected_not_connected(self, mock_connect):
        # Test ensure_connected when not connected
        db = DatabaseManager()
        db.pool = None
        
        await db._ensure_connected()
        
        mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_data_success(self):
        # Test successful stock data retrieval
        db = DatabaseManager()
        
        # Mock pool and connection
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock query result
        mock_records = [
            {"date": "2023-01-01", "close": 150.0, "volume": 1000000},
            {"date": "2023-01-02", "close": 155.0, "volume": 1100000}
        ]
        mock_connection.fetch.return_value = mock_records
        
        result = await db.get_stock_data("AAPL", "2023-01-01", "2023-01-02")
        
        assert len(result) == 2
        assert result[0]["close"] == 150.0
        assert result[1]["close"] == 155.0
        mock_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_data_no_data(self):
        # Test stock data retrieval with no data found
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock empty result
        mock_connection.fetch.return_value = []
        
        result = await db.get_stock_data("INVALID", "2023-01-01", "2023-01-02")
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_stock_data_database_error(self):
        # Test stock data retrieval with database error
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock database error
        mock_connection.fetch.side_effect = asyncpg.PostgreSQLError("Query failed")
        
        with pytest.raises(Exception):
            await db.get_stock_data("AAPL", "2023-01-01", "2023-01-02")
    
    @pytest.mark.asyncio
    async def test_validate_multiple_symbols_success(self):
        # Test successful multiple symbol validation
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock query result - symbols exist
        mock_connection.fetch.return_value = [
            {"symbol": "AAPL"},
            {"symbol": "GOOGL"}
        ]
        
        result = await db.validate_multiple_symbols(["AAPL", "GOOGL", "INVALID"])
        
        assert result["AAPL"] is True
        assert result["GOOGL"] is True
        assert result["INVALID"] is False
    
    @pytest.mark.asyncio
    async def test_validate_multiple_symbols_empty_list(self):
        # Test multiple symbol validation with empty list
        db = DatabaseManager()
        
        result = await db.validate_multiple_symbols([])
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_validate_multiple_symbols_database_error(self):
        # Test multiple symbol validation with database error
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetch.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await db.validate_multiple_symbols(["AAPL"])
    
    @pytest.mark.asyncio
    async def test_validate_date_range_has_data_success(self):
        # Test successful date range validation
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock query results
        mock_connection.fetchrow.side_effect = [
            {"count": 250},  # Record count query
            {"min_date": "2023-01-01", "max_date": "2023-12-31"}  # Date range query
        ]
        
        result = await db.validate_date_range_has_data("AAPL", "2023-01-01", "2023-12-31")
        
        assert result["has_data"] is True
        assert result["sufficient_data"] is True
        assert result["record_count"] == 250
        assert result["coverage_percentage"] > 90
    
    @pytest.mark.asyncio
    async def test_validate_date_range_has_data_no_data(self):
        # Test date range validation with no data
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock empty results
        mock_connection.fetchrow.side_effect = [
            {"count": 0},  # No records
            None  # No date range
        ]
        
        result = await db.validate_date_range_has_data("INVALID", "2023-01-01", "2023-12-31")
        
        assert result["has_data"] is False
        assert result["record_count"] == 0
    
    @pytest.mark.asyncio
    async def test_validate_date_range_has_data_insufficient_coverage(self):
        # Test date range validation with insufficient data coverage
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock low coverage scenario
        mock_connection.fetchrow.side_effect = [
            {"count": 100},  # Low record count
            {"min_date": "2023-01-01", "max_date": "2023-12-31"}
        ]
        
        result = await db.validate_date_range_has_data("AAPL", "2023-01-01", "2023-12-31")
        
        assert result["has_data"] is True
        assert result["sufficient_data"] is False  # Below 50% threshold
        assert result["coverage_percentage"] < 50
    
    @pytest.mark.asyncio
    async def test_validate_date_range_has_data_database_error(self):
        # Test date range validation with database error
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetchrow.side_effect = Exception("Database error")
        
        result = await db.validate_date_range_has_data("AAPL", "2023-01-01", "2023-12-31")
        
        assert "error" in result
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        # Test successful health check
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # Mock health check queries
        mock_connection.fetchrow.side_effect = [
            {"version": "PostgreSQL 13.0"},  # Version query
            {"symbols_daily": 50},           # Daily symbols count
            {"daily_records": 10000},        # Daily records count
            {"symbols_intraday": 25},        # Intraday symbols count
            {"intraday_records": 50000}      # Intraday records count
        ]
        
        result = await db.health_check()
        
        assert result["status"] == "healthy"
        assert result["database_version"] == "PostgreSQL 13.0"
        assert result["data_stats"]["symbols_daily"] == 50
        assert result["data_stats"]["daily_records"] == 10000
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self):
        # Test health check with connection error
        db = DatabaseManager()
        
        # Simulate connection failure
        with patch.object(db, '_ensure_connected', side_effect=Exception("Connection failed")):
            result = await db.health_check()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_query_error(self):
        # Test health check with query error
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        # First query succeeds, second fails
        mock_connection.fetchrow.side_effect = [
            {"version": "PostgreSQL 13.0"},
            Exception("Query failed")
        ]
        
        result = await db.health_check()
        
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Query failed" in result["error"]
    
    @pytest.mark.asyncio
    @patch('database.DatabaseManager._ensure_connected')
    async def test_get_stock_data_ensures_connection(self, mock_ensure_connected):
        # Test that get_stock_data ensures connection
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetch.return_value = []
        
        await db.get_stock_data("AAPL", "2023-01-01", "2023-01-02")
        
        mock_ensure_connected.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('database.DatabaseManager._ensure_connected')
    async def test_validate_multiple_symbols_ensures_connection(self, mock_ensure_connected):
        # Test that validate_multiple_symbols ensures connection
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetch.return_value = []
        
        await db.validate_multiple_symbols(["AAPL"])
        
        mock_ensure_connected.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('database.DatabaseManager._ensure_connected')
    async def test_validate_date_range_ensures_connection(self, mock_ensure_connected):
        # Test that validate_date_range_has_data ensures connection
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetchrow.return_value = {"count": 0}
        
        await db.validate_date_range_has_data("AAPL", "2023-01-01", "2023-01-02")
        
        mock_ensure_connected.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('database.DatabaseManager._ensure_connected')
    async def test_health_check_ensures_connection(self, mock_ensure_connected):
        # Test that health_check ensures connection
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetchrow.return_value = {"version": "PostgreSQL 13.0"}
        
        await db.health_check()
        
        mock_ensure_connected.assert_called_once()
    
    def test_connection_string_formation(self):
        # Test database connection string formation
        db = DatabaseManager()
        
        # Should contain expected components
        assert "postgresql://" in db.database_url
        assert "simulated_trading_platform" in db.database_url  # database name
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        # Test database connection context manager usage
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_pool.acquire.return_value.__aexit__.return_value = None
        db.pool = mock_pool
        
        # Test context manager behavior
        async with db.pool.acquire() as conn:
            assert conn == mock_connection
        
        # Verify acquire was called
        mock_pool.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        # Test that SQL queries are properly parameterized
        db = DatabaseManager()
        
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        db.pool = mock_pool
        
        mock_connection.fetch.return_value = []
        
        # Test with potentially dangerous input
        malicious_symbol = "AAPL'; DROP TABLE daily_prices; --"
        
        await db.get_stock_data(malicious_symbol, "2023-01-01", "2023-01-02")
        
        # Verify that the query was called with parameters (not string concatenation)
        mock_connection.fetch.assert_called_once()
        call_args = mock_connection.fetch.call_args
        
        # The query should use $1, $2, etc. for parameters, not string concatenation
        query = call_args[0][0]
        assert "$1" in query or "?" in query  # Parameterized query
        assert "DROP TABLE" not in query      # Malicious content not in query