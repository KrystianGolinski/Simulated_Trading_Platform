from database import get_database
from repositories.stock_data_repository import StockDataRepository
from services.temporal_validation_service import TemporalValidationService
from validation import SimulationValidator
from services.strategy_service_implementation import StrategyService

async def get_stock_data_repository() -> StockDataRepository:
    # Use shared database manager to avoid creating multiple connection pools
    db_manager = await get_database()
    return db_manager.stock_data_repository

async def get_temporal_validation_service() -> TemporalValidationService:
    # Service creation using shared repository
    stock_repo = await get_stock_data_repository()
    return TemporalValidationService(stock_repo)

async def get_strategy_service() -> StrategyService:
    # Strategy service creation with lazy loading
    return StrategyService()

async def get_simulation_validator() -> SimulationValidator:
    # Validator creation using shared repository and strategy service
    stock_repo = await get_stock_data_repository()
    strategy_service = await get_strategy_service()
    return SimulationValidator(stock_repo, strategy_service)