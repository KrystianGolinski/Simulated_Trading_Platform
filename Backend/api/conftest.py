import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from database import DatabaseManager
from services.error_handler import ErrorHandler
from models import SimulationConfig, StrategyType
from datetime import date

@pytest.fixture(scope="session")
def event_loop():
    # Create an instance of the default event loop for the test session
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db():
    # Mock database manager for testing
    db = AsyncMock(spec=DatabaseManager)
    
    # Mock common database responses
    db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True, "MSFT": True}
    db.validate_date_range_has_data.return_value = {
        "has_data": True,
        "sufficient_data": True,
        "coverage_percentage": 95.0,
        "record_count": 252,
        "expected_days": 265
    }
    db.health_check.return_value = {
        "status": "healthy",
        "data_stats": {
            "symbols_daily": 50,
            "daily_records": 10000
        }
    }
    
    return db

@pytest.fixture
def error_handler():
    # Error handler instance for testing
    return ErrorHandler()

@pytest.fixture
def sample_simulation_config():
    # Sample simulation configuration for testing
    return SimulationConfig(
        symbols=["AAPL", "GOOGL"],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        starting_capital=10000.0,
        strategy=StrategyType.MA_CROSSOVER,
        short_ma=10,
        long_ma=20
    )

@pytest.fixture
def sample_cpp_output():
    # Sample C++ engine output for testing
    return {
        "stdout": """
{
    "total_return": 15.5,
    "win_rate": 0.65,
    "total_trades": 25,
    "winning_trades": 16,
    "losing_trades": 9,
    "max_drawdown_pct": -8.2,
    "sharpe_ratio": 1.34,
    "final_portfolio_value": 11550.0
}
        """.strip(),
        "stderr": "",
        "return_code": 0
    }

@pytest.fixture
def sample_invalid_json():
    # Sample invalid JSON output for testing
    return '{"total_return": 15.5, "win_rate":}'  # Missing value

@pytest.fixture
def sample_cpp_error():
    # Sample C++ error output for testing.
    return {
        "stdout": "",
        "stderr": "Error: Failed to load historical data for symbol INVALID\nException: std::runtime_error - Database connection lost",
        "return_code": 1
    }