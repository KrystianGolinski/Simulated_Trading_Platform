# Services package for separated concerns
from .result_processor import ResultProcessor
from .error_handler import ErrorHandler
from .error_types import SimulationError, ErrorCode, ErrorSeverity
from .performance_calculator import PerformanceCalculator
from .trade_converter import TradeConverter
from .equity_processor import EquityProcessor
from .error_categorizers import (
    ErrorCategorizer, TimeoutErrorCategorizer, PermissionErrorCategorizer,
    MemoryErrorCategorizer, DiskSpaceErrorCategorizer, FileNotFoundErrorCategorizer,
    GenericErrorCategorizer, CppErrorExtractor
)

__all__ = [
    'ResultProcessor',
    'ErrorHandler', 
    'SimulationError',
    'ErrorCode',
    'ErrorSeverity',
    'PerformanceCalculator',
    'TradeConverter',
    'EquityProcessor',
    'ErrorCategorizer',
    'TimeoutErrorCategorizer',
    'PermissionErrorCategorizer',
    'MemoryErrorCategorizer',
    'DiskSpaceErrorCategorizer',
    'FileNotFoundErrorCategorizer',
    'GenericErrorCategorizer',
    'CppErrorExtractor'
]