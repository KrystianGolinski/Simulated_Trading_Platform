import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from services.error_handler import ErrorHandler
from repositories.stock_data_repository import StockDataRepository
from models import SimulationConfig, StrategyType
from datetime import date

@pytest.fixture(scope="session")
def event_loop():
    # Create an instance of the default event loop for the test session
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_stock_repo():
    # Mock stock data repository for testing
    repo = AsyncMock(spec=StockDataRepository)
    
    # Mock common repository responses
    repo.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True, "MSFT": True}
    repo.validate_date_range_has_data.return_value = {
        "has_data": True,
        "sufficient_data": True,
        "coverage_percentage": 95.0,
        "record_count": 252,
        "expected_days": 265
    }
    repo.get_available_stocks.return_value = (["AAPL", "GOOGL", "MSFT"], 3)
    repo.validate_symbol_exists.return_value = True
    repo.validate_stock_tradeable.return_value = True
    repo.get_eligible_stocks_for_period.return_value = ["AAPL", "GOOGL", "MSFT"]
    
    return repo

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
    # Sample C++ error output for testing
    return {
        "stdout": "",
        "stderr": "Error: Failed to load historical data for symbol INVALID\nException: std::runtime_error - Database connection lost",
        "return_code": 1
    }

@pytest.fixture
def mock_execution_service():
    # Mock execution service for testing
    service = MagicMock()
    service.start_simulation.return_value = "test-simulation-123"
    service.get_simulation_status.return_value = {
        "simulation_id": "test-simulation-123",
        "status": "RUNNING",
        "progress": 50.0,
        "started_at": "2023-01-01T10:00:00"
    }
    service.cancel_simulation.return_value = True
    service.test_engine_availability.return_value = {
        "available": True,
        "status": "ready",
        "version": "1.0.0"
    }
    return service

@pytest.fixture
def mock_result_processor():
    # Mock result processor for testing
    processor = MagicMock()
    processor.results_storage = {}
    processor.parse_json_result.return_value = {
        "starting_capital": 10000.0,
        "ending_value": 11550.0,
        "total_return_pct": 15.5
    }
    processor.validate_result_data.return_value = True
    return processor

@pytest.fixture
def sample_stock_data():
    # Sample stock data for testing
    return [
        {
            "date": "2023-01-01",
            "open": 150.0,
            "high": 155.0,
            "low": 148.0,
            "close": 152.0,
            "volume": 1000000
        },
        {
            "date": "2023-01-02", 
            "open": 152.0,
            "high": 158.0,
            "low": 151.0,
            "close": 156.0,
            "volume": 1200000
        }
    ]

@pytest.fixture
def sample_validation_result():
    # Sample validation result for testing
    return {
        "is_valid": True,
        "errors": [],
        "warnings": ["Date range is quite long - consider shorter periods for initial testing"]
    }

@pytest.fixture  
def sample_performance_metrics():
    # Sample performance metrics for testing
    return {
        "total_return_pct": 15.5,
        "sharpe_ratio": 1.34,
        "max_drawdown_pct": 8.2,
        "win_rate": 65.0,
        "total_trades": 25,
        "winning_trades": 16,
        "losing_trades": 9,
        "avg_return_per_trade": 0.62,
        "volatility": 12.3
    }

@pytest.fixture
def sample_trade_records():
    # Sample trade records for testing
    return [
        {
            "symbol": "AAPL",
            "action": "BUY@150.00 -> SELL@160.00 (+6.67%)",
            "quantity": 66,
            "entry_date": "2023-01-15",
            "exit_date": "2023-01-20",
            "total_value": 660.0,
            "commission": 2.0
        },
        {
            "symbol": "AAPL", 
            "action": "BUY@155.00 -> SELL@148.00 (-4.52%)",
            "quantity": 64,
            "entry_date": "2023-02-10",
            "exit_date": "2023-02-15", 
            "total_value": -448.0,
            "commission": 2.0
        }
    ]

@pytest.fixture
def sample_simulation_results():
    # Complete simulation results for testing
    return {
        "simulation_id": "test-sim-123",
        "status": "COMPLETED",
        "config": {
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "starting_capital": 10000.0,
            "strategy": "MA_CROSSOVER"
        },
        "starting_capital": 10000.0,
        "ending_value": 11550.0,
        "total_return_pct": 15.5,
        "performance_metrics": {
            "total_return_pct": 15.5,
            "sharpe_ratio": 1.34,
            "max_drawdown_pct": 8.2,
            "win_rate": 65.0,
            "total_trades": 25
        },
        "trades": [],
        "equity_curve": [
            {"date": "2023-01-01", "value": 10000.0},
            {"date": "2023-12-31", "value": 11550.0}
        ],
        "created_at": "2023-01-01T10:00:00",
        "started_at": "2023-01-01T10:01:00", 
        "completed_at": "2023-01-01T10:05:00"
    }

@pytest.fixture
def mock_strategy_registry():
    # Mock strategy registry for testing
    registry = MagicMock()
    registry.get_available_strategies.return_value = {
        "MA_CROSSOVER": {
            "name": "Moving Average Crossover",
            "description": "Simple moving average crossover strategy",
            "parameters": ["short_ma", "long_ma"],
            "category": "technical"
        },
        "RSI": {
            "name": "RSI Strategy", 
            "description": "RSI-based momentum strategy",
            "parameters": ["rsi_period", "rsi_oversold", "rsi_overbought"],
            "category": "technical"
        }
    }
    registry.get_strategy_categories.return_value = {
        "technical": ["MA_CROSSOVER", "RSI"],
        "fundamental": []
    }
    registry.validate_strategy_parameters.return_value = {"valid": True, "errors": []}
    return registry

@pytest.fixture
def mock_health_data():
    # Mock health check data for testing
    return {
        "status": "healthy",
        "timestamp": "2023-01-01T10:00:00",
        "database": {
            "status": "healthy",
            "connection_pool_size": 10,
            "active_connections": 2,
            "response_time_ms": 15.2
        },
        "validation_system": {
            "status": "healthy",
            "last_check": "2023-01-01T09:59:30"
        },
        "cpp_engine": {
            "status": "available",
            "version": "1.0.0",
            "last_test": "2023-01-01T09:58:00"
        },
        "system_resources": {
            "cpu_usage_percent": 25.3,
            "memory_usage_percent": 42.1,
            "disk_usage_percent": 68.9
        }
    }

@pytest.fixture
def sample_api_responses():
    # Sample API response structures for testing
    return {
        "success_response": {
            "success": True,
            "message": "Operation completed successfully",
            "data": {"result": "success"},
            "timestamp": "2023-01-01T10:00:00"
        },
        "error_response": {
            "success": False,
            "message": "Operation failed",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": "Invalid input parameters"
            },
            "timestamp": "2023-01-01T10:00:00"
        },
        "paginated_response": {
            "success": True,
            "data": [{"item": 1}, {"item": 2}],
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total": 2,
                "total_pages": 1
            },
            "timestamp": "2023-01-01T10:00:00"
        }
    }