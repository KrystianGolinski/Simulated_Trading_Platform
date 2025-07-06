# C++ Trading Engine Technical Documentation

## 1. Introduction

This document provides a technical overview of the C++ Trading Engine, a high-performance backtesting system.

### 1.1. Core Design Principles

-   **Performance**: Built with modern C++17 for high-speed, memory-efficient processing of large datasets.
-   **Modularity**: A service-oriented architecture with dependency injection allows components to be developed and tested in isolation.
-   **Separation of Concerns**: The engine is decomposed into specialized services (orchestration, strategy management, data processing, result calculation).
-   **Safety**: The `Result<T>` pattern is used for error handling in performance-critical paths, avoiding the overhead of exceptions.
-   **Temporal Accuracy**: A key design feature is the dynamic mitigation of survivorship bias, ensuring backtests are historically accurate.
-   **Extensibility**: The Strategy pattern allows new trading algorithms to be added with minimal friction.
-   **Progress Reporting**: Real-time progress updates via JSON streams on stderr for parallel execution coordination.

### 1.2. Key Components and Directory Mapping

#### Core Engine Components
-   `src/main.cpp`: Application entry point.
-   `src/trading_orchestrator.cpp`: The central orchestrator for all simulations.
-   `src/trading_engine.cpp`: Core service manager and container for other components.
-   `src/strategy_manager.cpp`: Manages strategy creation, validation, and execution.
-   `src/data_processor.cpp`: Handles data loading, validation, and processing.
-   `src/result_calculator.cpp`: Calculates performance metrics from simulation results.
-   `src/command_dispatcher.cpp`: Routes command-line arguments to the orchestrator.
-   `src/progress_service.cpp`: Manages real-time progress reporting via JSON on stderr.

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

#### Build and Test Configuration
-   `CMakeLists.txt`: The build configuration file.
-   `tests/`: Comprehensive test suite.

## 2. Architecture

### 2.1. High-Level Data Flow

1.  **Input**: The engine receives a request via command-line arguments, often including a path to a JSON configuration file.
2.  **Dispatch**: `CommandDispatcher` parses the input and routes it to the `TradingOrchestrator`.
3.  **Data Processing**: The `TradingOrchestrator` calls the `DataProcessor` to load, validate, and prepare historical market data.
4.  **Strategy Management**: The `TradingOrchestrator` uses the `StrategyManager` to create and configure the specified trading strategy.
5.  **Simulation Loop**: The `TradingOrchestrator` iterates through the historical data, day by day.
6.  **Temporal Validation**: On each day, the `DataProcessor` ensures that stocks are actively trading, dynamically handling IPOs and delistings to prevent survivorship bias.
7.  **Signal Generation**: Inside the loop, the `TradingOrchestrator` passes the current data to the `StrategyManager`, which executes the `TradingStrategy` to generate BUY, SELL, or HOLD signals.
8.  **Execution**: The `ExecutionService` processes these signals, creating orders that are fulfilled by the `Portfolio`.
9.  **Progress Updates**: During execution, `ProgressService` reports completion percentage via JSON on stderr at 5% intervals.
10. **Result Calculation**: After the simulation, the `TradingOrchestrator` passes the trade log to the `ResultCalculator`.
11. **Output**: The `ResultCalculator` computes the final performance metrics, which are then serialized to JSON by the `TradingOrchestrator` and printed to standard output.

### 2.2. Survivorship Bias Mitigation

The engine does not simply filter out delisted stocks at the start. Instead, it performs **dynamic temporal validation** on every day of a simulation:

-   It uses the `is_stock_tradeable()` database function to check if a stock was listed and not delisted on the current simulation date.
-   A stock is only included in strategy calculations for the days it was actively trading.
-   If a stock held in the portfolio is delisted, the engine automatically force-sells the position to simulate the real-world event.

## 3. Reference

### 3.1. Core Data Structures

-   **`SimulationConfig`**: Holds the complete configuration for a backtest, loaded from JSON.
-   **`PriceData`**: Represents a single OHLCV data point for a stock on a given day.
-   **`TradingSignal`**: Represents a BUY, SELL, or HOLD signal generated by a strategy.
-   **`BacktestResult`**: A comprehensive structure containing all performance metrics and trade logs from a completed simulation.

### 3.2. Key Classes and Responsibilities

-   **`TradingOrchestrator`**: The main service that orchestrates the entire backtest, managing the simulation lifecycle from initialization to result processing.
-   **`TradingEngine`**: Acts as a core service manager and container, holding instances of the various services (`DataProcessor`, `StrategyManager`, etc.) and managing the `Portfolio`. Its public methods delegate high-level tasks to the `TradingOrchestrator`.
-   **`StrategyManager`**: Responsible for the lifecycle of trading strategies, including instantiation, configuration, validation, and execution of signal generation.
-   **`DataProcessor`**: Handles all aspects of historical data management, including loading from the database, preprocessing, validation, and managing rolling data windows for strategies.
-   **`ResultCalculator`**: Calculates all performance and risk metrics from a completed simulation's trade log.
-   **`CommandDispatcher`**: Parses command-line arguments and dispatches commands to the `TradingOrchestrator`.
-   **`ArgumentParser`**: Handles the logic of parsing arguments and JSON files.
-   **`TradingStrategy`**: The interface for all trading algorithms.
-   **`Portfolio`**: Manages the simulation's cash and stock holdings.
-   **`Position`**: Represents a holding of a single stock.
-   **`MarketData`**: An abstraction layer over the database connection for fetching price data.
-   **`DatabaseConnection`**: Manages the low-level connection to PostgreSQL.
-   **`ExecutionService`**: Translates signals into portfolio actions.
-   **`ProgressService`**: Reports real-time progress via JSON on stderr, enabling parallel execution coordination.
-   **`Order`**: Represents buy/sell orders in the system.
-   **`PortfolioAllocator`**: Manages portfolio allocation strategies.
-   **`DataConversion`**: Handles data format conversions between systems.
-   **`TechnicalIndicators`**: Implements technical analysis indicators.
-   **`JsonHelpers`**: Utility functions for JSON serialization and parsing.
-   **`DateTimeUtils`**: Date and time manipulation utilities.
-   **`Logger`**: Comprehensive logging system.
-   **`ErrorUtils`**: Error handling and categorization utilities.

### 3.3. Error Handling

The engine uses a combination of the `Result<T>` pattern and a custom exception hierarchy.
-   **`Result<T>`**: Used for functions that can fail in a predictable way (e.g., a database query returning no rows). This avoids exception overhead in tight loops.
-   **`TradingException`**: A hierarchy of custom exceptions (`DatabaseException`, `StrategyException`, etc.) is used for unrecoverable or system-level errors.
-   **`ErrorUtils`**: Provides error categorization, logging, and handling utilities.

### 3.4. Technical Indicators

The engine includes a comprehensive set of technical indicators:
-   **Moving Averages**: Simple, exponential, and weighted moving averages.
-   **Momentum Indicators**: RSI, MACD, Stochastic oscillators.
-   **Volatility Indicators**: Bollinger Bands, Average True Range.
-   **Volume Indicators**: On-Balance Volume, Volume Price Trend.
-   **Trend Indicators**: ADX, Parabolic SAR, Ichimoku.

### 3.5. Data Management

#### Database Integration
-   **Connection Pooling**: Efficient database connection management.
-   **Query Optimization**: Prepared statements and query caching.
-   **Transaction Management**: ACID compliance for data integrity.
-   **Temporal Validation**: Dynamic IPO/delisting checks.

#### Data Conversion
-   **Format Standardization**: Consistent data format across components.
-   **Type Safety**: Strong typing for financial data.
-   **Validation**: Data integrity checks and sanitization.
-   **Caching**: In-memory caching for frequently accessed data.

### 3.6. Command-Line Interface

-   `--simulate`: Runs a simulation with parameters provided on the command line.
-   `--backtest`: Runs a simulation using a JSON configuration file.
-   `--test-db`: Tests the connection to the database.
-   `--status`: Checks the engine's status.

**Example JSON Configuration:**
```json
{
    "symbols": ["AAPL", "GOOGL"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "capital": 100000.0,
    "strategy": "ma_crossover",
    "strategy_parameters": {
        "short_period": 10,
        "long_period": 20
    }
}
```

### 3.7. Build Process

The engine is built using CMake.

1.  **Install Dependencies**: `sudo apt-get install build-essential cmake libpq-dev nlohmann-json3-dev`
2.  **Configure**: `cmake -B build`
3.  **Compile**: `cmake --build build -j$(nproc)`
4.  **Run Tests**: `cd build && ctest`
