# Dependency Injection Layer for FastAPI
# This file provides dependency injection functions for all API endpoints
# Key responsibilities:
# - Create and configure service instances for router injection
# - Manage service dependencies and lifecycle
# - Ensure shared database connections across services
# - Provide consistent service configuration throughout the application
# 
# All dependency functions are async and return configured service instances
# Used by FastAPI's dependency injection system via Depends()

from database import get_database
from repositories.stock_data_repository import StockDataRepository
from services.temporal_validation_service import TemporalValidationService
from validation import SimulationValidator
from services.strategy_service_implementation import StrategyService

async def get_stock_data_repository() -> StockDataRepository:
    # Provides the stock data repository instance for stock-related operations
    # Uses shared database manager to ensure efficient connection pooling
    # Repository pattern provides abstraction over database queries for stock data
    # Used by stock endpoints for symbol validation, price data, and temporal checks
    db_manager = await get_database()
    return db_manager.stock_data_repository

async def get_temporal_validation_service() -> TemporalValidationService:
    # Provides temporal validation service for stock trading period validation
    # Validates if stocks were tradeable during specified date ranges
    # Handles IPO dates, delisting dates, and trading suspension periods
    # Used by simulation validation and stock endpoints
    stock_repo = await get_stock_data_repository()
    return TemporalValidationService(stock_repo)

async def get_strategy_service() -> StrategyService:
    # Provides strategy service for trading strategy management
    # Handles strategy discovery, parameter validation, and configuration
    # Integrates with strategy registry for dynamic strategy loading
    # Used by strategy endpoints and simulation validation
    return StrategyService()

async def get_simulation_validator() -> SimulationValidator:
    # Provides comprehensive simulation configuration validator
    # Validates simulation parameters including:
    # - Stock symbol existence and temporal validity
    # - Strategy configuration and parameters
    # - Date range validation and market availability
    # - Capital and risk parameter validation
    # Used by simulation endpoints to ensure valid configurations
    stock_repo = await get_stock_data_repository()
    strategy_service = await get_strategy_service()
    return SimulationValidator(stock_repo, strategy_service)