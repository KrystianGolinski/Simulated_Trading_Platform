# C++ Trading Engine Technical Documentation

## 1. Introduction

This document provides a technical overview of the C++ Trading Engine, a high-performance backtesting system.

**Language Standard:** C++17 with modern STL features  
**Build System:** CMake with multi-target configuration  
**Container Integration:** Docker with shared volume access  
**Database Connectivity:** libpq (PostgreSQL C library) with connection management

### 1.1. Core Design Principles

-   **Performance**: Built with modern C++17 for high-speed, memory-efficient processing of large datasets with optimized algorithms.
-   **Modularity**: Service-oriented architecture with clear separation of concerns and isolated component development.
-   **Command Pattern**: Comprehensive command dispatcher supporting multiple execution modes (simulate, backtest, test, status).
-   **Safety**: The `Result<T>` pattern for error handling in performance-critical paths, avoiding exception overhead.
-   **Memory Management**: Smart pointers and RAII patterns for automatic resource management.
-   **Temporal Accuracy**: Dynamic survivorship bias mitigation ensuring historically accurate backtests.
-   **Extensibility**: Strategy pattern allows new trading algorithms with minimal code changes.
-   **Progress Reporting**: Real-time JSON progress streams on stderr for API coordination.
-   **Configuration Flexibility**: JSON-based configuration with command-line and file-based parameter input.
-   **Comprehensive Logging**: Multi-level logging system with configurable verbosity for debugging and monitoring.

### 1.2. Key Components and Directory Mapping

#### Core Engine Components
-   `src/main.cpp`: Application entry point with logging configuration
-   `src/command_dispatcher.cpp`: Command routing and execution management (`--simulate`, `--backtest`, `--test-db`, `--status`)
-   `src/trading_orchestrator.cpp`: Central orchestrator for all simulations with comprehensive workflow management
-   `src/trading_engine.cpp`: Core service manager and dependency container
-   `src/strategy_manager.cpp`: Strategy creation, validation, and execution management
-   `src/data_processor.cpp`: Data loading, validation, and temporal processing
-   `src/result_calculator.cpp`: Performance metrics calculation and analysis
-   `src/progress_service.cpp`: Real-time progress reporting via JSON on stderr for API integration

#### Strategy and Trading Components
-   `include/trading_strategy.h`: Abstract base class for all trading strategies.
-   `src/trading_strategy.cpp`: Base implementation for trading strategies.
-   `src/portfolio.cpp`: Manages cash and stock positions.
-   `src/position.cpp`: Represents individual stock positions.
-   `src/execution_service.cpp`: Handles trade execution and order management.
-   `src/order.cpp`: Order representation and management.
-   `src/portfolio_allocator.cpp`: Portfolio allocation strategies.

#### Data Management Components
-   `src/market_data.cpp`: Handles data retrieval from the database.
-   `src/database_connection.cpp`: Manages low-level database connections.
-   `src/data_conversion.cpp`: Data format conversion utilities.
-   `src/technical_indicators.cpp`: Technical analysis indicators.

#### Utility Components
-   `src/argument_parser.cpp`: Command-line argument parsing.
-   `src/date_time_utils.cpp`: Date and time utility functions.
-   `src/json_helpers.cpp`: JSON serialization and parsing utilities.
-   `src/logger.cpp`: Logging infrastructure.
-   `src/error_utils.cpp`: Error handling utilities.
-   `src/result.cpp`: Result type implementation.

#### Header Files
-   `include/result.h`: Defines the `Result<T>` type for error handling.
-   `include/trading_exceptions.h`: Exception hierarchy definitions.
-   `include/argument_parser.h`: Argument parsing interface.
-   `include/data_conversion.h`: Data conversion utilities.
-   `include/database_connection.h`: Database connection interface.
-   `include/date_time_utils.h`: Date/time utility functions.
-   `include/error_utils.h`: Error handling utilities.
-   `include/execution_service.h`: Trade execution interface.
-   `include/json_helpers.h`: JSON utility functions.
-   `include/logger.h`: Logging interface.
-   `include/order.h`: Order management interface.
-   `include/portfolio_allocator.h`: Portfolio allocation interface.
-   `include/position.h`: Position management interface.
-   `include/technical_indicators.h`: Technical indicators interface.
-   `include/memory_optimizable.h`: Memory optimization utilities and interfaces.
-   `include/command_dispatcher.h`: Command routing and execution management.
-   `include/market_data.h`: Market data retrieval and management interface.

#### Build and Test Configuration
-   `CMakeLists.txt`: The build configuration file.
-   `tests/`: Comprehensive test suite.

## 2. Architecture

### 2.0. Container Integration

**Docker Deployment:**
-   **Multi-stage Build**: Separate compilation and runtime environments for size optimization
-   **Shared Volume**: Trading engine binary deployed to shared volume for API access
-   **Health Checks**: Container health validation ensures binary availability
-   **Environment Configuration**: Database connectivity via environment variables
-   **Logging Integration**: Structured logging compatible with container orchestration

### 2.1. Engine Execution Flow

1.  **Command Processing**: Engine receives request via command-line with support for direct parameters or JSON configuration
2.  **Command Dispatch**: `CommandDispatcher` validates input and routes to appropriate execution method in `TradingOrchestrator`
3.  **Configuration Parsing**: Arguments parsed into `TradingConfig` structure with comprehensive validation
4.  **Database Connectivity**: `MarketData` establishes PostgreSQL connection using environment variables
5.  **Data Loading**: `DataProcessor` loads and validates historical market data with temporal accuracy checks
6.  **Strategy Initialization**: `StrategyManager` creates and configures trading strategy with parameter validation
7.  **Portfolio Setup**: `Portfolio` initialized with starting capital and position tracking
8.  **Simulation Loop**: `TradingOrchestrator` iterates through historical data chronologically
9.  **Temporal Validation**: Per-day validation ensures stocks are actively trading to prevent survivorship bias
10. **Signal Generation**: `TradingStrategy` processes market data to generate BUY/SELL/HOLD signals
11. **Order Execution**: `ExecutionService` processes signals and manages portfolio positions
12. **Progress Reporting**: `ProgressService` reports completion percentage via JSON on stderr for API monitoring
13. **Result Calculation**: `ResultCalculator` computes comprehensive performance metrics and risk analysis
14. **Output Generation**: Results serialized to JSON and output to stdout for API consumption

### 2.2. Survivorship Bias Mitigation

The engine does not simply filter out delisted stocks at the start. Instead, it performs **dynamic temporal validation** on every day of a simulation:

-   It uses the `is_stock_tradeable()` database function to check if a stock was listed and not delisted on the current simulation date.
-   A stock is only included in strategy calculations for the days it was actively trading.
-   If a stock held in the portfolio is delisted, the engine automatically force-sells the position to simulate the real-world event.

## 3. Reference

### 3.1. Core Data Structures

-   **`TradingConfig`**: Holds the complete configuration for a backtest, loaded from JSON.
-   **`PriceData`**: Represents a single OHLCV data point for a stock on a given day.
-   **`TradingSignal`**: Represents a BUY, SELL, or HOLD signal generated by a strategy.
-   **`BacktestResult`**: A comprehensive structure containing all performance metrics and trade logs from a completed simulation.

### 3.2. Core Engine Components

**Orchestration Layer:**
-   **`CommandDispatcher`**: Central command routing with support for multiple execution modes and comprehensive error handling
-   **`TradingOrchestrator`**: Main simulation orchestrator managing complete workflow from initialization to result processing
-   **`TradingEngine`**: Core service manager and dependency container with lifecycle management
-   **`ArgumentParser`**: Command-line and JSON configuration parsing with validation

**Strategy and Execution Layer:**
-   **`StrategyManager`**: Trading strategy lifecycle management with validation and execution coordination
-   **`TradingStrategy`**: Abstract base interface for all trading algorithms with extensible parameter support
-   **`ExecutionService`**: Signal-to-order translation and execution management
-   **`PortfolioAllocator`**: Position sizing and allocation strategy management

**Data Management Layer:**
-   **`DataProcessor`**: Historical data management with temporal validation and preprocessing
-   **`MarketData`**: Database abstraction layer with PostgreSQL connection management
-   **`DatabaseConnection`**: Low-level PostgreSQL connectivity with connection pooling and error handling
-   **`DataConversion`**: Data format conversion and standardization utilities

**Portfolio and Position Management:**
-   **`Portfolio`**: Cash and position management with comprehensive transaction tracking
-   **`Position`**: Individual stock position representation with cost basis and P&L calculation
-   **`Order`**: Buy/sell order representation and management

**Analytics and Reporting:**
-   **`ResultCalculator`**: Performance metrics calculation with risk analysis and statistical measures
-   **`ProgressService`**: Real-time progress reporting via JSON streams for API integration
-   **`TechnicalIndicators`**: Technical analysis indicator library (RSI, MACD, Bollinger Bands, etc.)

**Utility and Infrastructure:**
-   **`JsonHelpers`**: JSON serialization and parsing utilities with error handling
-   **`DateTimeUtils`**: Date and time manipulation with trading calendar support
-   **`Logger`**: Multi-level logging system with configurable output and correlation support
-   **`ErrorUtils`**: Error categorization, handling, and reporting utilities
-   **`Result<T>`**: Type-safe error handling pattern avoiding exception overhead

### 3.3. Error Handling Architecture

**Result Pattern Implementation:**
-   **`Result<T>`**: Type-safe error handling for predictable failures (database queries, validation, data processing)
-   **Performance**: Avoids exception overhead in tight simulation loops
-   **Composability**: Chainable error handling with automatic error propagation
-   **Type Safety**: Compile-time guarantee that errors are handled

**Exception Hierarchy:**
-   **`TradingException`**: Base class for all trading-specific exceptions
-   **`DatabaseException`**: Database connectivity and query failures
-   **`StrategyException`**: Strategy validation and execution errors
-   **`ValidationException`**: Parameter and configuration validation errors
-   **`ConfigurationException`**: System configuration and initialization errors

**Error Utilities:**
-   **`ErrorUtils`**: Error categorization, logging, and formatting utilities
-   **Error Codes**: Standardized error codes for API integration
-   **Context Preservation**: Error messages include context and stack information
-   **Recovery Strategies**: Graceful degradation and fallback mechanisms

### 3.4. Technical Analysis Library

**Comprehensive Indicator Set:**
-   **Moving Averages**: Simple (SMA), Exponential (EMA), and Weighted Moving Averages with configurable periods (2-200 days)
-   **Momentum Indicators**: RSI (14-day default), MACD with signal line and histogram, Stochastic oscillators (%K and %D), Rate of Change (ROC)
-   **Volatility Indicators**: Bollinger Bands with 2-standard deviation bands, Average True Range (ATR), Volatility Ratio
-   **Volume Indicators**: On-Balance Volume (OBV), Volume Price Trend (VPT), Volume Weighted Average Price (VWAP), Money Flow Index
-   **Trend Indicators**: ADX for trend strength measurement, Parabolic SAR with acceleration factor, Aroon Up/Down indicators

**Implementation Features:**
-   **Optimized Calculations**: Efficient rolling calculations with O(1) update complexity for most indicators
-   **Parameter Validation**: Comprehensive input validation with sensible defaults and mathematically valid range checking
-   **Historical Accuracy**: Indicators calculated with proper historical data alignment and look-ahead bias prevention
-   **Extensible Design**: Template-based indicator framework allowing easy addition of new indicators through standardized interface
-   **Memory Efficiency**: Circular buffer implementation for historical data storage with configurable window sizes

### 3.5. Data Management Architecture

#### Database Integration
-   **Connection Management**: PostgreSQL libpq integration with automatic reconnection and error handling
-   **Query Optimization**: Prepared statements with parameter binding for performance and security
-   **Transaction Support**: ACID-compliant transactions for data integrity during complex operations
-   **Temporal Validation**: Dynamic IPO/delisting checks using database functions for survivorship bias prevention
-   **Connection Environment**: Environment variable configuration for flexible deployment

#### Data Processing Pipeline
-   **Format Standardization**: Consistent OHLCV data format across all engine components
-   **Type Safety**: Strong C++ typing with compile-time checks for financial data structures
-   **Data Validation**: Comprehensive validation with range checking and sanity tests
-   **Memory Optimization**: Efficient data structures with minimal memory allocation
-   **Caching Strategy**: In-memory caching for frequently accessed symbols and date ranges

### 3.6. Command-Line Interface

**Primary Commands:**
-   `--simulate`: Run simulation with command-line parameters (direct execution mode)
-   `--simulate --config [json_string]`: Run simulation from JSON configuration string (API integration mode)
-   `--backtest [config_file]`: Run backtest using JSON configuration file (file-based mode)
-   `--test-db`: Test database connectivity and validate connection parameters
-   `--status`: Display engine status, version, and system information
-   `--memory-report`: Generate comprehensive memory usage report with allocation statistics and optimization recommendations

**Command Dispatcher Features:**
-   **Error Handling**: Comprehensive exception catching with detailed error messages
-   **Validation**: Parameter validation before execution with clear error reporting
-   **Header Information**: Version and system information display (except in API mode)
-   **Flexible Input**: Support for both command-line parameters and JSON configuration

**Configuration Examples:**

**JSON Configuration File:**
```json
{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "capital": 100000.0,
    "strategy": "ma_crossover",
    "strategy_parameters": {
        "short_period": 10,
        "long_period": 20,
        "signal_threshold": 0.02
    }
}
```

**Command Line Examples:**
```bash
# Direct simulation with parameters
./trading_engine --simulate --symbols AAPL,GOOGL --start-date 2023-01-01 --end-date 2023-12-31 --capital 100000 --strategy ma_crossover

# JSON configuration string (API mode)
./trading_engine --simulate --config '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-12-31","capital":10000,"strategy":"rsi"}'

# Test database connectivity
./trading_engine --test-db

# Get engine status and version information
./trading_engine --status

# Generate comprehensive memory usage report
./trading_engine --memory-report
```

### 3.7. Build Process and Dependencies

**Build System:** CMake 3.16+ with modern C++ configuration

**Dependencies:**
-   **System**: `build-essential`, `cmake`, `libpq-dev` (PostgreSQL client library)
-   **JSON Library**: `nlohmann/json` (v3.11.3) - auto-fetched if not available
-   **Threading**: C++ threads library for concurrent operations
-   **PostgreSQL**: libpq for database connectivity

**Build Commands:**
1.  **Configure**: `cmake -B build -DCMAKE_BUILD_TYPE=Release`
2.  **Compile**: `cmake --build build -j$(nproc)`
3.  **Debug Build**: `cmake -B build -DCMAKE_BUILD_TYPE=Debug`
4.  **Run Tests**: `cd build && ./test_comprehensive`

**Build Features:**
-   **Multi-Target**: Separate executables for main engine and comprehensive tests
-   **Optimization**: Release builds with -O3 optimization, debug builds with -g -O0
-   **Common Library Function**: Shared library linking for consistent dependencies
-   **Container Integration**: Docker-based build with shared volume deployment
