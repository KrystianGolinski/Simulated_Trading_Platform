# Pydantic Data Models for Trading Platform API
# This file defines all data models used across the API for:
# - Request/response validation and serialisation
# - Standardised API response structures
# - Simulation configuration and results
# - Trading performance metrics and records
# - Dynamic strategy type handling
# - Pagination and error handling

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

# Generic type variable for standardised response containers
T = TypeVar("T")


# Dynamic strategy type generation - strategies are loaded from registry
# This replaces the hardcoded enum with dynamic strategy discovery
# Allows the API to support plugin-based strategies without code changes
def get_available_strategy_types():
    # Dynamically discover available strategies from the strategy registry
    # This enables plugin-based strategy architecture where new strategies
    # can be added without modifying the core API models
    try:
        from strategy_registry import get_strategy_registry

        registry = get_strategy_registry()
        strategies = registry.get_available_strategies()
        return {strategy_id: strategy_id for strategy_id in strategies.keys()}
    except ImportError:
        # Fallback to core strategies if registry not available
        # This ensures the API remains functional even if strategy registry fails
        return {"ma_crossover": "ma_crossover", "rsi": "rsi"}


class StrategyType(str, Enum):
    # Dynamic strategy enumeration based on registered strategies
    # Supports both core strategies and dynamically discovered plugin strategies
    @classmethod
    def _missing_(cls, value):
        # Allow dynamic strategy values not explicitly defined
        # This enables validation of plugin strategies at runtime
        available_strategies = get_available_strategy_types()
        if value in available_strategies:
            return value
        return None

    # Core strategies (always available as fallback)
    MA_CROSSOVER = "ma_crossover"
    RSI = "rsi"


class SimulationStatus(str, Enum):
    # Simulation lifecycle states used by simulation engine
    # These states are tracked in the database and returned by status endpoints
    PENDING = "pending"  # Simulation queued but not yet started
    RUNNING = "running"  # Simulation actively executing (may be parallel)
    COMPLETED = "completed"  # Simulation finished successfully with results
    FAILED = "failed"  # Simulation failed due to error (see error_message)


class SimulationConfig(BaseModel):
    # Core simulation configuration model used by /simulation/start endpoint
    # Validated against database constraints and strategy requirements
    symbols: List[str] = Field(
        ..., min_items=1, max_items=50, description="Stock symbols to simulate"
    )
    start_date: date = Field(..., description="Start date for simulation")
    end_date: date = Field(..., description="End date for simulation")
    starting_capital: float = Field(
        10000.0, gt=0, le=1000000, description="Starting capital in USD"
    )
    strategy: str = Field(
        ..., description="Trading strategy to use (dynamic strategy ID)"
    )

    # Dynamic strategy parameters - allows arbitrary strategy-specific parameters
    # Each strategy can define its own parameter schema for flexible configuration
    strategy_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy-specific parameters"
    )

    @model_validator(mode="after")
    def validate_model(self):
        # Centralized validation logic - consolidates duplicate validation from validation.py

        # Critical validation: end_date after start_date
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

        # Critical validation: no future dates
        # Cannot simulate trading in the future as historical data is required
        today = date.today()
        if self.start_date > today or self.end_date > today:
            raise ValueError("Dates cannot be in the future")

        # Basic symbol validation - consolidated from validation service
        # Note: More detailed validation (database existence) happens in validation service
        if not self.symbols:
            raise ValueError("At least one stock symbol is required for simulation")

        # Check for duplicate symbols (case-insensitive)
        unique_symbols = set(s.upper().strip() for s in self.symbols if s.strip())
        clean_symbols = [s.strip() for s in self.symbols if s.strip()]

        if len(unique_symbols) != len(clean_symbols):
            duplicates = [s for s in clean_symbols if clean_symbols.count(s) > 1]
            raise ValueError(
                f'Duplicate symbols are not allowed: {", ".join(set(duplicates))}'
            )

        # Basic format validation - lenient for compatibility
        for symbol in self.symbols:
            if not symbol or not symbol.strip():
                raise ValueError("Empty or whitespace symbols are not allowed")
            # Basic length check only - detailed format validation in validation service
            if len(symbol.strip()) > 10:
                raise ValueError(f"Symbol too long: {symbol} (max 10 characters)")

        return self

    @field_validator("symbols")
    @classmethod
    def symbols_uppercase(cls, v):
        # Normalise stock symbols to uppercase for consistent database queries
        return [symbol.upper() for symbol in v]


class TradeRecord(BaseModel):
    # Individual trade record returned by C++ simulation engine
    # Used in simulation results and performance analysis
    date: str  # Trade execution date (YYYY-MM-DD format)
    symbol: str  # Stock symbol (e.g., "AAPL")
    action: str  # Trade action: "BUY" or "SELL"
    shares: int  # Number of shares traded
    price: float  # Price per share at execution
    total_value: float  # Total trade value (shares * price)


class PerformanceMetrics(BaseModel):
    # Comprehensive performance metrics calculated by C++ simulation engine
    # Used for strategy evaluation and optimization analysis

    # Core metrics that C++ engine provides
    total_return_pct: float  # Total return percentage over simulation period
    sharpe_ratio: Optional[float] = None  # Risk-adjusted return metric
    max_drawdown_pct: float  # Maximum percentage loss from peak
    win_rate: float  # Percentage of profitable trades
    total_trades: int  # Total number of trades executed
    winning_trades: int  # Number of profitable trades
    losing_trades: int  # Number of losing trades

    # Additional metrics that C++ engine provides but we weren't using
    final_balance: Optional[float] = None  # Final portfolio value
    starting_capital: Optional[float] = None  # Initial capital amount
    max_drawdown: Optional[float] = None  # Absolute value, not percentage

    # Computed metrics we could add
    profit_factor: Optional[float] = None  # winning_trades_value / losing_trades_value
    average_win: Optional[float] = None  # Average profit per winning trade
    average_loss: Optional[float] = None  # Average loss per losing trade

    # Fields that might be useful but C++ doesn't provide yet
    annualized_return: Optional[float] = None  # Return adjusted for time period
    volatility: Optional[float] = None  # Portfolio volatility measure

    # Signals-related metrics
    signals_generated: Optional[int] = None  # Number of strategy signals generated


class ValidationError(BaseModel):
    # Detailed validation error for specific fields
    # Used by validation services to provide precise error feedback
    field: str  # Field name that failed validation
    message: str  # Human-readable error message
    error_code: str  # Machine-readable error code for client handling


class ValidationResult(BaseModel):
    # Comprehensive validation result containing errors and warnings
    # Used by validation endpoints and internal validation services
    is_valid: bool  # Overall validation status
    errors: List[ValidationError] = []  # List of validation errors (blocking)
    warnings: List[str] = []  # List of validation warnings (non-blocking)


class SimulationResults(BaseModel):
    # Complete simulation results model returned by /simulation/{id}/results
    # Contains all simulation data including performance metrics and execution metadata
    simulation_id: str  # Unique simulation identifier
    status: SimulationStatus  # Current simulation status
    config: SimulationConfig  # Original simulation configuration

    # Results (only present when status is COMPLETED)
    starting_capital: Optional[float] = None  # Initial capital amount
    ending_value: Optional[float] = None  # Final portfolio value
    total_return_pct: Optional[float] = None  # Overall return percentage
    performance_metrics: Optional[PerformanceMetrics] = (
        None  # Detailed performance analysis
    )
    trades: Optional[List[TradeRecord]] = None  # Individual trade records
    equity_curve: Optional[List[Dict[str, Any]]] = None  # Portfolio value over time

    # Execution info
    created_at: datetime  # When simulation was created
    started_at: Optional[datetime] = None  # When simulation execution began
    completed_at: Optional[datetime] = None  # When simulation finished
    error_message: Optional[str] = None  # Error details if simulation failed

    # Memory tracking (added for memory optimization analysis)
    memory_statistics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Memory usage statistics captured during simulation execution",
    )

    # Optimization tracking (added for parallel execution analysis)
    optimization_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optimization metadata including actual vs estimated speedup for parallel execution",
    )


class SimulationResponse(BaseModel):
    # Response model for simulation start endpoint
    # Provides immediate feedback when simulation is queued
    simulation_id: str  # Unique identifier for tracking
    status: SimulationStatus  # Initial status (typically PENDING)
    message: str  # Success/error message


class SimulationStatusResponse(BaseModel):
    # Real-time simulation status response for /simulation/{id}/status
    # Supports both sequential and parallel execution progress tracking
    simulation_id: str  # Unique simulation identifier
    status: SimulationStatus  # Current execution status
    progress_pct: Optional[float] = None  # Overall progress percentage (0-100)
    current_date: Optional[str] = None  # Current date being processed
    elapsed_time: Optional[float] = None  # Time elapsed since start (seconds)
    estimated_remaining: Optional[float] = None  # Estimated time remaining (seconds)


# Response Models - Standardised API response structures
# All API endpoints use these models for consistent response format
# Follows the standard: {status, message, data, errors, warnings, metadata}


class ResponseStatus(str, Enum):
    # Standard response status values used across all endpoints
    SUCCESS = "success"  # Operation completed successfully
    ERROR = "error"  # Operation failed with errors
    WARNING = "warning"  # Operation succeeded but with warnings


class ApiError(BaseModel):
    # Detailed error information for client-side error handling
    # Used in error arrays within StandardResponse
    code: str  # Machine-readable error code
    message: str  # Human-readable error message
    field: Optional[str] = None  # Field name if error is field-specific
    details: Optional[Dict[str, Any]] = None  # Additional error context


class StandardResponse(BaseModel, Generic[T]):
    # Standard response container used by all API endpoints
    # Provides consistent structure for success/error handling
    status: ResponseStatus  # Response status indicator
    message: str  # Primary response message
    data: Optional[T] = None  # Response payload (typed)
    errors: Optional[List[ApiError]] = None  # Detailed error information
    warnings: Optional[List[str]] = None  # Non-blocking warnings
    metadata: Optional[Dict[str, Any]] = None  # Additional response metadata


class PaginationInfo(BaseModel):
    # Pagination metadata for list endpoints
    # Provides all information needed for client-side pagination controls
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, le=1000, description="Number of items per page")
    total_count: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    # Standard paginated response for list endpoints
    # Extends StandardResponse with pagination information
    status: ResponseStatus  # Response status indicator
    message: str  # Primary response message
    data: List[T]  # List of typed items
    pagination: PaginationInfo  # Pagination metadata
    errors: Optional[List[ApiError]] = None  # Detailed error information
    warnings: Optional[List[str]] = None  # Non-blocking warnings
    metadata: Optional[Dict[str, Any]] = None  # Additional response metadata


# Response helper functions
# These utility functions ensure consistent response formatting across all endpoints
# Used by RouterBase and response formatters to create standardised responses


def create_success_response(
    data: T,
    message: str = "Success",
    warnings: List[str] = None,
    metadata: Dict[str, Any] = None,
) -> StandardResponse[T]:
    # Create a successful response with optional warnings and metadata
    # Used for successful operations that may have non-blocking warnings
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata,
    )


def create_error_response(
    message: str, errors: List[ApiError] = None, status_code: int = 400
) -> StandardResponse[None]:
    # Create an error response with detailed error information
    # Used by exception handlers and validation failures
    return StandardResponse(
        status=ResponseStatus.ERROR, message=message, errors=errors or [], data=None
    )


def create_warning_response(
    data: T, message: str, warnings: List[str], metadata: Dict[str, Any] = None
) -> StandardResponse[T]:
    # Create a warning response for operations that succeed but have issues
    # Used when operations complete but with non-optimal conditions
    return StandardResponse(
        status=ResponseStatus.WARNING,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata,
    )


def create_paginated_response(
    data: List[T],
    page: int,
    page_size: int,
    total_count: int,
    message: str = "Success",
    warnings: List[str] = None,
    metadata: Dict[str, Any] = None,
) -> PaginatedResponse[T]:
    # Create a paginated response with calculated pagination metadata
    # Used by list endpoints to provide consistent pagination information

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
        has_previous=has_previous,
    )

    return PaginatedResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        pagination=pagination_info,
        warnings=warnings,
        metadata=metadata,
    )
