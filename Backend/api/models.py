from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum

class StrategyType(str, Enum):
    MA_CROSSOVER = "ma_crossover"
    RSI = "rsi"

class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationConfig(BaseModel):
    symbols: List[str] = Field(..., min_items=1, max_items=20, description="Stock symbols to simulate")
    start_date: date = Field(..., description="Start date for simulation")
    end_date: date = Field(..., description="End date for simulation")
    starting_capital: float = Field(10000.0, gt=0, le=1000000, description="Starting capital in USD")
    strategy: StrategyType = Field(StrategyType.MA_CROSSOVER, description="Trading strategy to use")
    
    # Strategy-specific parameters
    short_ma: Optional[int] = Field(20, gt=0, le=200, description="Short moving average period")
    long_ma: Optional[int] = Field(50, gt=0, le=200, description="Long moving average period")
    rsi_period: Optional[int] = Field(14, gt=0, le=100, description="RSI period")
    rsi_oversold: Optional[float] = Field(30.0, gt=0, lt=100, description="RSI oversold threshold")
    rsi_overbought: Optional[float] = Field(70.0, gt=0, lt=100, description="RSI overbought threshold")
    
    @model_validator(mode='after')
    def validate_model(self):
        # Basic validation only - comprehensive validation handled by validation.py
        
        # Critical validation: end_date after start_date
        if self.end_date <= self.start_date:
            raise ValueError('End date must be after start date')
        
        # Critical validation: no future dates
        today = date.today()
        if self.start_date > today or self.end_date > today:
            raise ValueError('Dates cannot be in the future')
        
        # Critical validation: MA parameters if provided
        if self.strategy == StrategyType.MA_CROSSOVER and self.short_ma and self.long_ma:
            if self.long_ma <= self.short_ma:
                raise ValueError('Long MA must be greater than short MA')
        
        # Note: Comprehensive validation is handled by SimulationValidator in validation.py
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
    total_return_pct: float
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int

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