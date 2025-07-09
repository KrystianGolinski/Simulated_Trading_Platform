# Services Package - Comprehensive Business Logic and Error Handling Services
# This package provides specialized services for the Trading Platform API with clear separation of concerns
#
# Architecture Overview:
# The services package implements a sophisticated service layer that handles core business logic,
# error management, and data processing for the trading platform. It provides specialized services
# for result processing, performance calculations, error handling, and C++ engine integration.
#
# Key Service Categories:
# 1. Result Processing Services - Handle simulation output processing and conversion
# 2. Error Handling Services - Comprehensive error categorization and management
# 3. Performance Services - Trading performance calculations and analytics
# 4. Data Processing Services - Trade and equity data transformation
# 5. Validation Services - Temporal and business logic validation
# 6. Engine Integration Services - C++ engine interaction and error extraction
#
# Service Architecture Principles:
# - Single Responsibility: Each service has a focused, well-defined purpose
# - Dependency Injection: Services are designed for easy testing and mocking
# - Error Handling: Comprehensive error categorization and context preservation
# - Performance: Optimized for high-throughput simulation processing
# - Extensibility: Plugin-based architecture for strategy and error categorization
#
# Integration with Trading Platform:
# - Provides core business logic layer between API controllers and data access
# - Integrates with C++ trading engine for simulation execution
# - Supports parallel execution optimization and performance monitoring
# - Implements comprehensive error handling for distributed system reliability
#
# Error Handling Framework:
# The services package includes a sophisticated error handling framework that:
# - Categorizes errors by type and severity for appropriate response handling
# - Preserves detailed context information for debugging and monitoring
# - Provides actionable suggestions for error resolution
# - Maintains error history for pattern analysis and system health monitoring
from .equity_processor import EquityProcessor
from .error_categorizers import (
    CppErrorExtractor,
    DiskSpaceErrorCategorizer,
    ErrorCategorizer,
    FileNotFoundErrorCategorizer,
    GenericErrorCategorizer,
    MemoryErrorCategorizer,
    PermissionErrorCategorizer,
    TimeoutErrorCategorizer,
)
from .error_handler import ErrorHandler
from .error_types import ErrorCode, ErrorSeverity, SimulationError
from .performance_calculator import PerformanceCalculator
from .result_processor import ResultProcessor
from .trade_converter import TradeConverter

__all__ = [
    "ResultProcessor",
    "ErrorHandler",
    "SimulationError",
    "ErrorCode",
    "ErrorSeverity",
    "PerformanceCalculator",
    "TradeConverter",
    "EquityProcessor",
    "ErrorCategorizer",
    "TimeoutErrorCategorizer",
    "PermissionErrorCategorizer",
    "MemoryErrorCategorizer",
    "DiskSpaceErrorCategorizer",
    "FileNotFoundErrorCategorizer",
    "GenericErrorCategorizer",
    "CppErrorExtractor",
]
