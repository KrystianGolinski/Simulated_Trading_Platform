import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from validation import SimulationValidator
from models import SimulationConfig, ValidationError, ValidationResult, StrategyType

class TestSimulationValidator:
    
    def test_init(self, mock_db):
        # Test SimulationValidator initialization
        validator = SimulationValidator(mock_db)
        assert validator.db == mock_db
        assert validator.error_handler is not None
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_success(self, mock_db, sample_simulation_config):
        # Test successful simulation configuration validation
        validator = SimulationValidator(mock_db)
        
        # Mock successful database responses
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True}
        mock_db.validate_date_range_has_data.return_value = {
            "has_data": True,
            "sufficient_data": True,
            "coverage_percentage": 95.0,
            "record_count": 252,
            "expected_days": 265
        }
        
        result = await validator.validate_simulation_config(sample_simulation_config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        # May have warnings about old dates, which is fine
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_symbol_errors(self, mock_db, sample_simulation_config):
        # Test simulation validation with symbol errors
        validator = SimulationValidator(mock_db)
        
        # Mock invalid symbols
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": False}
        
        result = await validator.validate_simulation_config(sample_simulation_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("GOOGL" in error.message for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_symbols_empty(self, mock_db):
        # Test validation with empty symbols list
        validator = SimulationValidator(mock_db)
        
        # Test the _validate_symbols method directly since Pydantic prevents empty list
        errors = await validator._validate_symbols([])
        
        assert len(errors) == 1
        assert errors[0].error_code == "SYMBOLS_EMPTY"
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_duplicate_symbols(self, mock_db):
        # Test validation with duplicate symbols
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL", "aapl"],  # Duplicate symbols (case insensitive)
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        result = await validator.validate_simulation_config(config)
        
        assert result.is_valid is False
        assert any(error.error_code == "SYMBOLS_DUPLICATE" for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_low_capital(self, mock_db):
        # Test validation with low starting capital
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=500.0,  # Below minimum
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True}
        
        result = await validator.validate_simulation_config(config)
        
        assert result.is_valid is False
        assert any(error.error_code == "CAPITAL_TOO_LOW" for error in result.errors)
    
    def test_validate_capital_too_high(self, mock_db):
        # Test capital validation with excessively high capital
        validator = SimulationValidator(mock_db)
        
        # Test the _validate_capital method directly since Pydantic prevents > 1M
        errors = validator._validate_capital(15_000_000.0)
        
        assert len(errors) == 1
        assert errors[0].error_code == "CAPITAL_TOO_HIGH"
    
    def test_validate_strategy_parameters_invalid_ma(self, mock_db):
        # Test validation with invalid moving average parameters
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=2,   # Too low (will be allowed by Pydantic but caught by validator)
            long_ma=180   # Within Pydantic limit but will be caught by validator for being too high
        )
        
        errors = validator._validate_strategy_parameters(config)
        
        assert len(errors) >= 1
        assert any(error.error_code == "SHORT_MA_TOO_LOW" for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_invalid_rsi_parameters(self, mock_db):
        # Test validation with invalid RSI parameters
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.RSI,
            rsi_period=3,        # Too low
            rsi_oversold=5,      # Too low
            rsi_overbought=95    # Too high
        )
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True}
        
        result = await validator.validate_simulation_config(config)
        
        assert result.is_valid is False
        assert any(error.error_code == "RSI_PERIOD_TOO_LOW" for error in result.errors)
        assert any(error.error_code == "RSI_OVERSOLD_TOO_LOW" for error in result.errors)
        assert any(error.error_code == "RSI_OVERBOUGHT_TOO_HIGH" for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_no_data_available(self, mock_db, sample_simulation_config):
        # Test validation when no data is available for date range
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True}
        mock_db.validate_date_range_has_data.return_value = {
            "has_data": False,
            "record_count": 0,
            "expected_days": 265
        }
        
        result = await validator.validate_simulation_config(sample_simulation_config)
        
        assert result.is_valid is False
        assert any(error.error_code == "NO_DATA_AVAILABLE" for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_insufficient_data_warning(self, mock_db, sample_simulation_config):
        # Test validation with insufficient but present data generates warning
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True}
        mock_db.validate_date_range_has_data.return_value = {
            "has_data": True,
            "sufficient_data": False,
            "coverage_percentage": 45.0,  # Below 50% threshold
            "record_count": 120,
            "expected_days": 265
        }
        
        result = await validator.validate_simulation_config(sample_simulation_config)
        
        assert result.is_valid is True  # Still valid, just warning
        assert len(result.warnings) > 0
        assert any("45.0%" in warning for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_database_error(self, mock_db, sample_simulation_config):
        # Test validation with database error
        validator = SimulationValidator(mock_db)
        
        # Simulate database error
        mock_db.validate_multiple_symbols.side_effect = Exception("Database connection lost")
        
        result = await validator.validate_simulation_config(sample_simulation_config)
        
        assert result.is_valid is False
        assert any(error.error_code == "DATABASE_ERROR" for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_simulation_config_validation_system_error(self, mock_db):
        # Test validation with system error in validation process
        validator = SimulationValidator(mock_db)
        
        # Create a config that will cause an exception
        invalid_config = None  # This will cause an AttributeError
        
        result = await validator.validate_simulation_config(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Validation system error" in result.errors[0].message
    
    @pytest.mark.asyncio
    async def test_validate_symbols_success(self, mock_db):
        # Test successful symbol validation
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "GOOGL": True}
        
        errors = await validator._validate_symbols(["AAPL", "GOOGL"])
        
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_symbols_not_found(self, mock_db):
        # Test symbol validation with symbol not found
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_multiple_symbols.return_value = {"AAPL": True, "INVALID": False}
        
        errors = await validator._validate_symbols(["AAPL", "INVALID"])
        
        assert len(errors) == 1
        assert errors[0].error_code == "SYMBOL_NOT_FOUND"
        assert "INVALID" in errors[0].message
    
    @pytest.mark.asyncio
    async def test_validate_date_ranges_success(self, mock_db, sample_simulation_config):
        # Test successful date range validation
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_date_range_has_data.return_value = {
            "has_data": True,
            "sufficient_data": True,
            "coverage_percentage": 95.0
        }
        
        result = await validator._validate_date_ranges(sample_simulation_config)
        
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_date_ranges_database_error(self, mock_db, sample_simulation_config):
        # Test date range validation with database error
        validator = SimulationValidator(mock_db)
        
        mock_db.validate_date_range_has_data.return_value = {
            "error": "Database connection failed"
        }
        
        result = await validator._validate_date_ranges(sample_simulation_config)
        
        assert len(result["errors"]) > 0
        assert any(error.error_code == "DATABASE_ERROR" for error in result["errors"])
    
    def test_validate_capital_success(self, mock_db):
        # Test successful capital validation
        validator = SimulationValidator(mock_db)
        
        errors = validator._validate_capital(10000.0)
        
        assert len(errors) == 0
    
    def test_validate_capital_zero(self, mock_db):
        # Test capital validation with zero capital
        validator = SimulationValidator(mock_db)
        
        errors = validator._validate_capital(0.0)
        
        assert len(errors) == 2  # CAPITAL_INVALID and CAPITAL_TOO_LOW
        assert any(error.error_code == "CAPITAL_INVALID" for error in errors)
    
    def test_validate_capital_negative(self, mock_db):
        # Test capital validation with negative capital
        validator = SimulationValidator(mock_db)
        
        errors = validator._validate_capital(-1000.0)
        
        assert len(errors) == 2  # CAPITAL_INVALID and CAPITAL_TOO_LOW
        assert any(error.error_code == "CAPITAL_INVALID" for error in errors)
    
    def test_validate_strategy_parameters_ma_crossover(self, mock_db):
        # Test strategy parameter validation for MA crossover
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        errors = validator._validate_strategy_parameters(config)
        
        assert len(errors) == 0
    
    def test_validate_strategy_parameters_rsi(self, mock_db):
        # Test strategy parameter validation for RSI
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.RSI,
            rsi_period=14,
            rsi_oversold=30,
            rsi_overbought=70
        )
        
        errors = validator._validate_strategy_parameters(config)
        
        assert len(errors) == 0
    
    def test_check_configuration_warnings_short_date_range(self, mock_db):
        # Test configuration warnings for short date range
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 12, 20),   # Only 11 days (very short)
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        warnings = validator._check_configuration_warnings(config)
        
        assert len(warnings) >= 1  # May have additional warnings
        assert any("Short date range" in warning for warning in warnings)
    
    def test_check_configuration_warnings_long_date_range(self, mock_db):
        # Test configuration warnings for very long date range
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2018, 1, 1),   # More than 5 years
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        warnings = validator._check_configuration_warnings(config)
        
        assert len(warnings) > 0
        assert any("Very long date range" in warning for warning in warnings)
    
    def test_check_configuration_warnings_close_ma_periods(self, mock_db):
        # Test configuration warnings for close MA periods
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            starting_capital=10000.0,
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=12  # Too close to short_ma
        )
        
        warnings = validator._check_configuration_warnings(config)
        
        assert len(warnings) > 0
        assert any("MA periods are close" in warning for warning in warnings)
    
    def test_check_configuration_warnings_low_capital_long_period(self, mock_db):
        # Test configuration warnings for low capital with long time period
        validator = SimulationValidator(mock_db)
        
        config = SimulationConfig(
            symbols=["AAPL"],
            start_date=date(2022, 1, 1),   # More than 1 year
            end_date=date(2023, 12, 31),
            starting_capital=5000.0,       # Low capital
            strategy=StrategyType.MA_CROSSOVER,
            short_ma=10,
            long_ma=20
        )
        
        warnings = validator._check_configuration_warnings(config)
        
        assert len(warnings) > 0
        assert any("Low starting capital" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_check_database_connection_healthy(self, mock_db):
        # Test database connection check when healthy
        validator = SimulationValidator(mock_db)
        
        mock_db.health_check.return_value = {
            "status": "healthy",
            "data_stats": {
                "symbols_daily": 50,
                "daily_records": 10000
            }
        }
        
        result = await validator.check_database_connection()
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_check_database_connection_unhealthy(self, mock_db):
        # Test database connection check when unhealthy
        validator = SimulationValidator(mock_db)
        
        mock_db.health_check.return_value = {
            "status": "unhealthy",
            "error": "Connection timeout"
        }
        
        result = await validator.check_database_connection()
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "DATABASE_UNHEALTHY"
    
    @pytest.mark.asyncio
    async def test_check_database_connection_limited_data_warnings(self, mock_db):
        # Test database connection check with limited data warnings
        validator = SimulationValidator(mock_db)
        
        mock_db.health_check.return_value = {
            "status": "healthy",
            "data_stats": {
                "symbols_daily": 5,    # Limited symbols
                "daily_records": 500   # Limited records
            }
        }
        
        result = await validator.check_database_connection()
        
        assert result.is_valid is True
        assert len(result.warnings) == 2  # Both symbols and records warnings
        assert any("Limited symbol data" in warning for warning in result.warnings)
        assert any("Limited historical data" in warning for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_check_database_connection_exception(self, mock_db):
        # Test database connection check with exception
        validator = SimulationValidator(mock_db)
        
        mock_db.health_check.side_effect = Exception("Connection failed")
        
        result = await validator.check_database_connection()
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "DATABASE_CONNECTION_ERROR"