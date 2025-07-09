# Pytest Configuration and Test Fixtures
# This file provides comprehensive test fixtures for the Trading Platform API
# Key responsibilities:
# - Async event loop configuration for testing
# - Mock service instances for unit testing
# - Sample data fixtures for consistent test scenarios
# - Test response structures for API endpoint testing
# - Mock strategy and execution services
# - Health check and performance data fixtures

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from models import SimulationConfig, StrategyType
from repositories.stock_data_repository import StockDataRepository
from services.error_handler import ErrorHandler


@pytest.fixture(scope="session")
def event_loop():
    # Create an instance of the default event loop for the test session
    # This fixture ensures consistent async behaviour across all tests
    # Scoped to session level to avoid creating multiple event loops
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_stock_repo():
    # Mock stock data repository for testing
    # Provides realistic responses for common stock data operations
    # Used by validation services, temporal validation, and simulation endpoints
    repo = AsyncMock(spec=StockDataRepository)

    # Mock common repository responses for symbol validation
    repo.validate_multiple_symbols.return_value = {
        "AAPL": True,
        "GOOGL": True,
        "MSFT": True,
    }

    # Mock data availability responses for date range validation
    repo.validate_date_range_has_data.return_value = {
        "has_data": True,  # Data exists for the period
        "sufficient_data": True,  # Coverage is adequate for simulation
        "coverage_percentage": 95.0,  # 95% data coverage
        "record_count": 252,  # Trading days with data
        "expected_days": 265,  # Expected trading days in period
    }

    # Mock stock listing and temporal validation responses
    repo.get_available_stocks.return_value = (["AAPL", "GOOGL", "MSFT"], 3)
    repo.validate_symbol_exists.return_value = True
    repo.validate_stock_tradeable.return_value = True
    repo.get_eligible_stocks_for_period.return_value = ["AAPL", "GOOGL", "MSFT"]

    return repo


@pytest.fixture
def error_handler():
    # Error handler instance for testing error categorisation and messaging
    # Used by validation services and simulation engine for structured error handling
    return ErrorHandler()


@pytest.fixture
def sample_simulation_config():
    # Sample simulation configuration for testing validation and execution
    # Represents a typical multi-symbol simulation with moving average crossover strategy
    # Used by simulation validation tests and simulation engine tests
    return SimulationConfig(
        symbols=["AAPL", "GOOGL"],  # Multi-symbol portfolio simulation
        start_date=date(2023, 1, 1),  # Full year simulation period
        end_date=date(2023, 12, 31),
        starting_capital=10000.0,  # Standard starting capital
        strategy=StrategyType.MA_CROSSOVER,  # Well-tested strategy
        strategy_parameters={  # Strategy-specific parameters
            "short_ma": 10,
            "long_ma": 20,
        },
    )


@pytest.fixture
def sample_cpp_output():
    # Sample C++ trading engine output for testing result processing
    # Represents successful simulation execution with realistic performance metrics
    # Used by result processor tests and simulation engine integration tests
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
        "stderr": "",  # No errors from C++ engine
        "return_code": 0,  # Successful execution
    }


@pytest.fixture
def sample_invalid_json():
    # Sample invalid JSON output for testing error handling
    # Used to test JSON parsing error scenarios in result processing
    return '{"total_return": 15.5, "win_rate":}'  # Missing value - malformed JSON


@pytest.fixture
def sample_cpp_error():
    # Sample C++ engine error output for testing error categorisation
    # Represents typical engine failures with detailed error information
    # Used by error handler tests and simulation failure scenarios
    return {
        "stdout": "",  # No successful output
        "stderr": "Error: Failed to load historical data for symbol INVALID\nException: std::runtime_error - Database connection lost",
        "return_code": 1,  # Error exit code
    }


@pytest.fixture
def mock_execution_service():
    # Mock execution service for testing simulation lifecycle operations
    # Provides realistic responses for simulation start, status, and cancellation
    # Used by simulation engine tests and simulation router tests
    service = MagicMock()

    # Mock simulation lifecycle operations
    service.start_simulation.return_value = "test-simulation-123"
    service.get_simulation_status.return_value = {
        "simulation_id": "test-simulation-123",
        "status": "RUNNING",
        "progress": 50.0,
        "started_at": "2023-01-01T10:00:00",
    }
    service.cancel_simulation.return_value = True

    # Mock engine availability testing
    service.test_engine_availability.return_value = {
        "available": True,
        "status": "ready",
        "version": "1.0.0",
    }
    return service


@pytest.fixture
def mock_result_processor():
    # Mock result processor for testing simulation result handling
    # Provides consistent responses for result parsing and validation
    # Used by simulation engine tests and result processing workflow tests
    processor = MagicMock()
    processor.results_storage = {}  # In-memory storage for test results

    # Mock result parsing and validation
    processor.parse_json_result.return_value = {
        "starting_capital": 10000.0,
        "ending_value": 11550.0,
        "total_return_pct": 15.5,
    }
    processor.validate_result_data.return_value = True
    return processor


@pytest.fixture
def sample_stock_data():
    # Sample historical stock price data for testing
    # Represents typical OHLCV data structure used by the trading engine
    # Used by stock data repository tests and market data validation tests
    return [
        {
            "date": "2023-01-01",  # Trading date in YYYY-MM-DD format
            "open": 150.0,  # Opening price
            "high": 155.0,  # Daily high price
            "low": 148.0,  # Daily low price
            "close": 152.0,  # Closing price
            "volume": 1000000,  # Trading volume
        },
        {
            "date": "2023-01-02",
            "open": 152.0,
            "high": 158.0,
            "low": 151.0,
            "close": 156.0,
            "volume": 1200000,
        },
    ]


@pytest.fixture
def sample_validation_result():
    # Sample validation result structure for testing validation workflows
    # Represents successful validation with non-blocking warnings
    # Used by validation service tests and simulation configuration validation
    return {
        "is_valid": True,  # Overall validation status
        "errors": [],  # No blocking errors found
        "warnings": [
            "Date range is quite long - consider shorter periods for initial testing"
        ],  # Advisory warnings
    }


@pytest.fixture
def sample_performance_metrics():
    # Sample comprehensive performance metrics for testing analytics
    # Represents realistic trading strategy performance data
    # Used by performance calculator tests and result analysis tests
    return {
        "total_return_pct": 15.5,  # Overall return percentage
        "sharpe_ratio": 1.34,  # Risk-adjusted return metric
        "max_drawdown_pct": 8.2,  # Maximum loss from peak
        "win_rate": 65.0,  # Percentage of profitable trades
        "total_trades": 25,  # Total number of trades executed
        "winning_trades": 16,  # Number of profitable trades
        "losing_trades": 9,  # Number of losing trades
        "avg_return_per_trade": 0.62,  # Average return per trade
        "volatility": 12.3,  # Portfolio volatility measure
    }


@pytest.fixture
def sample_trade_records():
    # Sample individual trade execution records for testing trade analysis
    # Represents both profitable and losing trades with complete trade details
    # Used by trade logging tests and portfolio performance analysis
    return [
        {
            "symbol": "AAPL",
            "action": "BUY@150.00 -> SELL@160.00 (+6.67%)",  # Profitable trade description
            "quantity": 66,  # Number of shares traded
            "entry_date": "2023-01-15",  # Trade entry date
            "exit_date": "2023-01-20",  # Trade exit date
            "total_value": 660.0,  # Total profit/loss
            "commission": 2.0,  # Trading commission
        },
        {
            "symbol": "AAPL",
            "action": "BUY@155.00 -> SELL@148.00 (-4.52%)",  # Losing trade description
            "quantity": 64,
            "entry_date": "2023-02-10",
            "exit_date": "2023-02-15",
            "total_value": -448.0,  # Negative value for loss
            "commission": 2.0,
        },
    ]


@pytest.fixture
def sample_simulation_results():
    # Complete simulation results structure for testing end-to-end workflows
    # Represents fully processed simulation with all metadata and performance data
    # Used by simulation results endpoints and result aggregation tests
    return {
        "simulation_id": "test-sim-123",  # Unique simulation identifier
        "status": "COMPLETED",  # Final simulation status
        "config": {  # Original simulation configuration
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "starting_capital": 10000.0,
            "strategy": "MA_CROSSOVER",
        },
        "starting_capital": 10000.0,  # Initial portfolio value
        "ending_value": 11550.0,  # Final portfolio value
        "total_return_pct": 15.5,  # Overall performance
        "performance_metrics": {  # Detailed performance analysis
            "total_return_pct": 15.5,
            "sharpe_ratio": 1.34,
            "max_drawdown_pct": 8.2,
            "win_rate": 65.0,
            "total_trades": 25,
        },
        "trades": [],  # Individual trade records
        "equity_curve": [  # Portfolio value over time
            {"date": "2023-01-01", "value": 10000.0},
            {"date": "2023-12-31", "value": 11550.0},
        ],
        "created_at": "2023-01-01T10:00:00",  # Simulation lifecycle timestamps
        "started_at": "2023-01-01T10:01:00",
        "completed_at": "2023-01-01T10:05:00",
    }


@pytest.fixture
def mock_strategy_registry():
    # Mock strategy registry for testing dynamic strategy discovery and validation
    # Provides realistic strategy metadata for strategy management tests
    # Used by strategy service tests and strategy validation workflows
    registry = MagicMock()

    # Mock available strategies with comprehensive metadata
    registry.get_available_strategies.return_value = {
        "MA_CROSSOVER": {
            "name": "Moving Average Crossover",
            "description": "Simple moving average crossover strategy",
            "parameters": ["short_ma", "long_ma"],
            "category": "technical",
        },
        "RSI": {
            "name": "RSI Strategy",
            "description": "RSI-based momentum strategy",
            "parameters": ["rsi_period", "rsi_oversold", "rsi_overbought"],
            "category": "technical",
        },
    }

    # Mock strategy categorisation for filtering
    registry.get_strategy_categories.return_value = {
        "technical": ["MA_CROSSOVER", "RSI"],
        "fundamental": [],
    }

    # Mock parameter validation responses
    registry.validate_strategy_parameters.return_value = {"valid": True, "errors": []}
    return registry


@pytest.fixture
def mock_health_data():
    # Mock comprehensive system health check data for testing monitoring endpoints
    # Represents healthy system state across all components
    # Used by health check endpoint tests and system monitoring tests
    return {
        "status": "healthy",  # Overall system health status
        "timestamp": "2023-01-01T10:00:00",
        "database": {  # Database layer health metrics
            "status": "healthy",
            "connection_pool_size": 10,
            "active_connections": 2,
            "response_time_ms": 15.2,
        },
        "validation_system": {  # Validation service health
            "status": "healthy",
            "last_check": "2023-01-01T09:59:30",
        },
        "cpp_engine": {  # C++ trading engine status
            "status": "available",
            "version": "1.0.0",
            "last_test": "2023-01-01T09:58:00",
        },
        "system_resources": {  # System resource utilisation
            "cpu_usage_percent": 25.3,
            "memory_usage_percent": 42.1,
            "disk_usage_percent": 68.9,
        },
    }


@pytest.fixture
def sample_api_responses():
    # Sample standardised API response structures for testing endpoint consistency
    # Represents the standard response format used across all API endpoints
    # Used by API integration tests and response formatting tests
    return {
        "success_response": {  # Standard successful operation response
            "success": True,
            "message": "Operation completed successfully",
            "data": {"result": "success"},
            "timestamp": "2023-01-01T10:00:00",
        },
        "error_response": {  # Standard error response structure
            "success": False,
            "message": "Operation failed",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": "Invalid input parameters",
            },
            "timestamp": "2023-01-01T10:00:00",
        },
        "paginated_response": {  # Standard paginated list response
            "success": True,
            "data": [{"item": 1}, {"item": 2}],
            "pagination": {"page": 1, "per_page": 50, "total": 2, "total_pages": 1},
            "timestamp": "2023-01-01T10:00:00",
        },
    }
