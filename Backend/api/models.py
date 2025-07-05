from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime, date, timedelta
from enum import Enum

T = TypeVar('T')

# Dynamic strategy type generation - strategies are loaded from registry
# This replaces the hardcoded enum with dynamic strategy discovery
def get_available_strategy_types():
    try:
        from strategy_registry import get_strategy_registry
        registry = get_strategy_registry()
        strategies = registry.get_available_strategies()
        return {strategy_id: strategy_id for strategy_id in strategies.keys()}
    except ImportError:
        # Fallback to core strategies if registry not available
        return {"ma_crossover": "ma_crossover", "rsi": "rsi"}

class StrategyType(str, Enum):
    # Dynamic strategy enumeration based on registered strategies
    @classmethod
    def _missing_(cls, value):
        # Allow dynamic strategy values not explicitly defined
        available_strategies = get_available_strategy_types()
        if value in available_strategies:
            return value
        return None
    
    # Core strategies (always available)
    MA_CROSSOVER = "ma_crossover"
    RSI = "rsi"

class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationConfig(BaseModel):
    symbols: List[str] = Field(..., min_items=1, max_items=50, description="Stock symbols to simulate")
    start_date: date = Field(..., description="Start date for simulation")
    end_date: date = Field(..., description="End date for simulation")
    starting_capital: float = Field(10000.0, gt=0, le=1000000, description="Starting capital in USD")
    strategy: str = Field(..., description="Trading strategy to use (dynamic strategy ID)")
    
    # Dynamic strategy parameters - allows arbitrary strategy-specific parameters
    strategy_parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")
    
    @model_validator(mode='after')
    def validate_model(self):
        # Basic validation only - extensive validation handled by validation.py
        
        # Critical validation: end_date after start_date
        if self.end_date <= self.start_date:
            raise ValueError('End date must be after start date')
        
        # Critical validation: no future dates
        today = date.today()
        if self.start_date > today or self.end_date > today:
            raise ValueError('Dates cannot be in the future')
        
        return self
    
    @field_validator('symbols')
    @classmethod
    def symbols_uppercase(cls, v):
        return [symbol.upper() for symbol in v]

class TradeRecord(BaseModel):
    date: str
    symbol: str
    action: str  # BUY, SELL
    shares: int
    price: float
    total_value: float

class PerformanceMetrics(BaseModel):
    # Core metrics that C++ engine provides
    total_return_pct: float
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    # Additional metrics that C++ engine provides but we weren't using
    final_balance: Optional[float] = None
    starting_capital: Optional[float] = None
    max_drawdown: Optional[float] = None  # Absolute value, not percentage
    
    # Computed metrics we could add
    profit_factor: Optional[float] = None  # winning_trades_value / losing_trades_value
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    
    # Fields that might be useful but C++ doesn't provide yet
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    
    # Signals-related metrics
    signals_generated: Optional[int] = None

class ValidationError(BaseModel):
    field: str
    message: str
    error_code: str

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[str] = []

class SimulationResults(BaseModel):
    simulation_id: str
    status: SimulationStatus
    config: SimulationConfig
    
    # Results (only present when status is COMPLETED)
    starting_capital: Optional[float] = None
    ending_value: Optional[float] = None
    total_return_pct: Optional[float] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    trades: Optional[List[TradeRecord]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None
    
    # Execution info
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SimulationResponse(BaseModel):
    simulation_id: str
    status: SimulationStatus
    message: str

class SimulationStatusResponse(BaseModel):
    simulation_id: str
    status: SimulationStatus
    progress_pct: Optional[float] = None
    current_date: Optional[str] = None
    elapsed_time: Optional[float] = None
    estimated_remaining: Optional[float] = None

# Response Models - Standardised API response structures

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ApiError(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class StandardResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: Optional[T] = None
    errors: Optional[List[ApiError]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class PaginationInfo(BaseModel):
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, le=1000, description="Number of items per page")
    total_count: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

class PaginatedResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: List[T]
    pagination: PaginationInfo
    errors: Optional[List[ApiError]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

# Response helper functions

def create_success_response(data: T, message: str = "Success", warnings: List[str] = None, metadata: Dict[str, Any] = None) -> StandardResponse[T]:
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata
    )

def create_error_response(message: str, errors: List[ApiError] = None, status_code: int = 400) -> StandardResponse[None]:
    return StandardResponse(
        status=ResponseStatus.ERROR,
        message=message,
        errors=errors or [],
        data=None
    )

def create_warning_response(data: T, message: str, warnings: List[str], metadata: Dict[str, Any] = None) -> StandardResponse[T]:
    return StandardResponse(
        status=ResponseStatus.WARNING,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata
    )

def create_paginated_response(
    data: List[T], 
    page: int, 
    page_size: int, 
    total_count: int, 
    message: str = "Success",
    warnings: List[str] = None,
    metadata: Dict[str, Any] = None
) -> PaginatedResponse[T]:
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1
    
    pagination_info = PaginationInfo(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )
    
    return PaginatedResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        pagination=pagination_info,
        warnings=warnings,
        metadata=metadata
    )