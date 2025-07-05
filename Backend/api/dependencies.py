from database import get_database
from repositories.stock_data_repository import StockDataRepository
from services.temporal_validation_service import TemporalValidationService
from validation import SimulationValidator

async def get_stock_data_repository() -> StockDataRepository:
    # Use shared database manager to avoid creating multiple connection pools
    db_manager = await get_database()
    return db_manager.stock_data_repository

async def get_temporal_validation_service() -> TemporalValidationService:
    # Service creation using shared repository
    stock_repo = await get_stock_data_repository()
    return TemporalValidationService(stock_repo)

async def get_simulation_validator() -> SimulationValidator:
    # Validator creation using shared repository
    stock_repo = await get_stock_data_repository()
    return SimulationValidator(stock_repo)