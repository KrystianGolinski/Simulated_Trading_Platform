# Engine Structure Documentation

## Overview

The C++ Trading Engine is a high-performance backtesting system that executes trading strategies against historical market data. Built using modern C++17 with PostgreSQL integration, it follows service-oriented architecture principles with appropriate error handling and modular design.

## Architecture Components

### Core Engine Layer

#### `main.cpp`
Simple entry point that configures logging and delegates execution to CommandDispatcher
- **Purpose**: Application bootstrap
- **Dependencies**: logger.h, command_dispatcher.h
- **Output**: Process exit code

#### `trading_engine.h/cpp`
Central orchestrator managing the entire simulation/backtest process with dynamic temporal validation
- **Key Methods**:
  - `runBacktest(BacktestConfig)`: Execute single symbol backtest
  - `runBacktestMultiSymbol(symbols, dates, capital)`: Execute multi-asset backtest
  - `runSimulationWithParams(symbol, start_date, end_date, capital)`: Execute simulation with parameters
  - `runSimulationMultiSymbol(symbols, dates, capital)`: Multi-symbol simulation
  - `getPortfolioStatus()`: Get current portfolio state
  - `getExecutedSignals()`: Retrieve executed trading signals
  - `getBacktestResultsAsJson(result)`: Convert results to JSON format
- **Features**:
  - Dependency injection for testability
  - Memory optimisation and caching
  - Result<T> pattern for error handling
  - Progress reporting integration
  - Real-time IPO/delisting checking during trading loop
- **Dependencies**: All core services (portfolio, market_data, execution_service, progress_service, strategies)

##### Dynamic Survivorship Bias Mitigation
- **Validation Approach**: Uses dynamic inclusion rather than static exclusion
- **Real-time Checking**: Each trading day, validates if stocks are tradeable using `checkStockTradeable()`
- **Automatic Delisting Handling**: Force-sells positions when stocks become non-tradeable
- **IPO Integration**: Stocks only start trading after their actual IPO dates
- **Performance Optimised**: Database functions used for efficient temporal queries

### Command Processing Layer

#### `command_dispatcher.h/cpp`
Routes command-line commands to appropriate execution paths
- **Supported Commands**:
  - `--simulate`: Run trading simulation
  - `--backtest`: Execute backtesting mode
  - `--test-db`: Database connectivity test
  - `--status`: Engine status check
- **Input**: Command line arguments
- **Output**: Structured JSON results

#### `argument_parser.h/cpp`
Parses command-line arguments and JSON configuration files
- **Input Formats**:
  - Command line flags and values
  - JSON configuration files
- **Output**: `SimulationConfig` structs (handles both single and multi-symbol configurations)
- **Validation**: Parameter bounds checking and format validation

### Strategy System

#### `trading_strategy.h/cpp`
Abstract base class and concrete strategy implementations
- **Base Interface**:
  ```cpp
  class TradingStrategy {
  public:
      explicit TradingStrategy(const std::string& name);
      virtual ~TradingStrategy() = default;
      virtual TradingSignal evaluateSignal(const std::vector<PriceData>& price_data,
                                          const Portfolio& portfolio,
                                          const std::string& symbol = "") = 0;
      virtual void configure(const StrategyConfig& config);
      virtual bool validateConfig() const = 0;
      virtual std::string getDescription() const = 0;
  };
  ```
- **Implemented Strategies**:
  - **MovingAverageCrossoverStrategy**: SMA crossover signals
    - Parameters: short_period, long_period
    - Signals: BUY when short > long, SELL when short < long
  - **RSIStrategy**: RSI-based momentum signals
    - Parameters: rsi_period, oversold_threshold, overbought_threshold
    - Signals: BUY on oversold, SELL on overbought
- **Plugin Architecture**: Easy addition of new strategies through inheritance

### Portfolio Management

#### `portfolio.h/cpp`
Manages cash balance and stock positions
- **Key Methods**:
  - `buyStock(symbol, shares, price)`: Process buy orders
  - `sellStock(symbol, shares, price)`: Process sell orders
  - `sellAllStock(symbol, price)`: Liquidate entire position
  - `getTotalValue(current_prices)`: Calculate portfolio value
  - `getCashBalance()`: Current cash position
  - `hasPosition(symbol)`: Check if position exists
  - `getPosition(symbol)`: Retrieve specific position
- **Features**:
  - Multi-symbol position tracking
  - Commission and fee calculations
  - Position sizing controls

#### `position.h/cpp`
Individual stock position tracking
- **Attributes**:
  - `symbol`: Stock ticker
  - `shares`: Number of shares held
  - `average_cost`: Average purchase price
  - `unrealised_pnl`: Current profit/loss

#### `order.h/cpp`
Order execution and management
- **Order Types**: Market orders (limit orders future expansion)
- **Execution Logic**: Immediate execution at current market price
- **Validation**: Sufficient cash/shares verification

### Data Management Layer

#### `market_data.h/cpp`
Interface to PostgreSQL/TimescaleDB for historical price data
- **Key Methods**:
  - `getHistoricalPrices(symbol, start_date, end_date)`: Retrieve OHLCV data
  - `getAvailableSymbols()`: List all available stocks
  - `getDateRange(symbol)`: Get data availability dates
  - `getCurrentPrices()`: Get current market prices
  - `symbolExists(symbol)`: Validate symbol availability
  - `getLatestPrice(symbol)`: Get most recent price
- **Features**:
  - Connection pooling
  - Query optimisation
  - Data caching

#### `database_connection.h/cpp`
Low-level PostgreSQL connectivity with temporal validation
- **Connection Management**: Connection pooling and retry logic
- **Query Execution**: Prepared statements and result processing
- **Error Handling**: Database-specific exception handling

##### Core Database Methods
- `getStockPrices(symbol, start_date, end_date)`: Retrieve historical price data
- `getAvailableSymbols()`: Get list of all available stock symbols
- `checkSymbolExists(symbol)`: Validate symbol existence in database

##### Temporal Validation Methods
- **`checkStockTradeable(symbol, check_date)`**: Check if stock was tradeable on specific date
  - Uses database function `is_stock_tradeable()` for IPO/delisting validation
  - Returns boolean indicating trading eligibility
  - Essential for dynamic temporal validation during backtesting

- **`getEligibleStocksForPeriod(start_date, end_date)`**: Get stocks eligible for entire period
  - Uses database function `get_eligible_stocks_for_period()`
  - Returns list of symbols that were tradeable throughout period
  - Used for batch temporal validation

- **`getStockTemporalInfo(symbol)`**: Get temporal information
  - Returns IPO date, listing date, delisting date, trading status
  - Provides context for temporal validation decisions
  - Used for error reporting

- **`validateSymbolsForPeriod(symbols, start_date, end_date)`**: Batch temporal validation
  - Validates multiple symbols efficiently
  - Returns detailed validation results with IPO/delisting context
  - Optimised for large-scale simulations

#### `data_conversion.h/cpp`
Converts between database formats and internal structures
- **Conversions**:
  - Database rows → OHLCV structs
  - JSON configs → C++ configuration objects
  - Results → JSON output format
- **Type Safety**: Compile-time type checking for conversions

### Technical Analysis

#### `technical_indicators.h/cpp`
Implements common technical analysis indicators
- **Available Indicators**:
  - **Simple Moving Average (SMA)**: `calculate_sma(prices, period)`
  - **Exponential Moving Average (EMA)**: `calculate_ema(prices, period)`
  - **Relative Strength Index (RSI)**: `calculate_rsi(prices, period)`
  - **Bollinger Bands**: `calculate_bollinger_bands(prices, period, std_dev)`
- **Performance Features**:
  - Result caching for expensive calculations
  - Parallel calculation capabilities
  - Memory-efficient sliding window algorithms
- **Signal Detection**: Built-in crossover and threshold detection

### Execution System

#### `execution_service.h/cpp`
Handles buy/sell signal execution
- **Signal Processing**: Converts strategy signals to portfolio orders
- **Risk Management**: Position sizing and risk controls
- **Order Routing**: Interfaces with portfolio for trade execution

#### `progress_service.h/cpp`
Progress reporting for long-running simulations
- **Metrics Tracked**:
  - Percentage completion
  - Elapsed time
  - Estimated time remaining
  - Current processing date
- **Output**: JSON progress updates for API integration

### Infrastructure and Utilities

#### `result.h/cpp`
Monadic Result<T> pattern for adequate error handling
- **Usage Pattern**:
  ```cpp
  Result<PortfolioValue> calculate_value() {
      if (error_condition) {
          return Result<PortfolioValue>::error("Error message");
      }
      return Result<PortfolioValue>::success(portfolio_value);
  }
  ```
- **Benefits**: Eliminates exceptions in performance-critical paths
- **Chaining**: Monadic operations for complex error-prone workflows

#### `trading_exceptions.h`
Hierarchical exception system with specific error types
- **Exception Hierarchy**:
  - `TradingException`: Base exception class
  - `DatabaseException`: Database connectivity/query errors
  - `StrategyException`: Strategy configuration/execution errors
  - `PortfolioException`: Portfolio management errors
  - `ValidationException`: Input validation errors

#### `error_utils.h/cpp`
Error handling utilities and logging integration
- **Error Categorisation**: Systematic error classification
- **Recovery Strategies**: Automatic retry and fallback mechanisms
- **Logging Integration**: Structured error logging with context

#### `logger.h/cpp`
Configurable logging system
- **Log Levels**: DEBUG, INFO, WARN, ERROR, FATAL
- **Output Targets**: Console, file, structured JSON
- **Performance**: Low-overhead logging with compile-time level filtering

#### `json_helpers.h/cpp`
JSON serialisation/deserialisation utilities using nlohmann::json
- **Supported Types**: All engine data structures
- **Custom Serialisers**: Optimised serialisation for complex types
- **Validation**: JSON schema validation for input configurations

## Build System and Configuration

### `CMakeLists.txt`
CMake configuration with dependency management
- **Dependencies**:
  - PostgreSQL (libpq-dev)
  - nlohmann::json
  - C++17 compiler support
- **Build Targets**:
  - `trading_engine`: Main executable
  - `engine_tests`: Test suite
- **Compiler Flags**: Optimisation and warning configurations

### `build.sh`
Build automation script
- **Build Process**: CMake configuration, compilation, linking
- **Logging**: Build progress and error reporting
- **Cleanup**: Automated cleanup of build artifacts

### `Dockerfile`
Containerisation support for deployment
- **Base Image**: Ubuntu with build dependencies
- **Multi-stage Build**: Optimised production image
- **Runtime Dependencies**: PostgreSQL client libraries

## Testing Framework

### `test_comprehensive.cpp`
Comprehensive test suite covering all engine components
- **Test Categories**:
  - Unit tests for individual components
  - Integration tests for component interactions
  - End-to-end simulation tests
  - Performance benchmarks
- **Coverage**: All public interfaces and critical paths

### `engine_testing.sh`
Test automation and reporting
- **Test Execution**: Automated test discovery and execution
- **Reporting**: JUnit-compatible test reports
- **Performance Testing**: Benchmark execution and comparison

## Key Design Patterns

### Service-Oriented Architecture
- **Dependency Injection**: Services injected into TradingEngine for testability
- **Interface Segregation**: Clean interfaces between components
- **Inversion of Control**: Dependencies managed at application level

### Strategy Pattern
- **Pluggable Strategies**: Common interface for all trading strategies
- **Runtime Strategy Selection**: Dynamic strategy loading
- **Parameter Configuration**: Flexible strategy parameterisation

### Result Pattern
- **Functional Error Handling**: Eliminates exceptions in core paths
- **Composable Operations**: Monadic chaining for complex workflows
- **Explicit Error States**: Clear success/failure semantics

### RAII (Resource Acquisition Is Initialisation)
- **Automatic Resource Management**: Smart pointers for memory management
- **Exception Safety**: Guaranteed cleanup in error conditions
- **Database Connections**: Automatic connection lifecycle management

## Data Flow Architecture

### Input Processing
1. **Command Line Arguments** → `ArgumentParser` → `SimulationConfig`
2. **JSON Configuration Files** → `ArgumentParser` → `SimulationConfig`
3. **API Requests** → JSON → `ArgumentParser` → `SimulationConfig`

### Execution Flow
1. **Command Routing**: `CommandDispatcher` determines execution mode
2. **Data Retrieval**: `MarketData` fetches historical prices from database
3. **Strategy Evaluation**: `TradingStrategy` generates buy/sell signals
4. **Signal Processing**: `ExecutionService` processes signals
5. **Portfolio Updates**: `Portfolio` executes trades and updates positions
6. **Performance Calculation**: `TradingEngine` calculates metrics
7. **Result Serialisation**: `json_helpers` converts results to JSON

### Output Generation
1. **Performance Metrics** → JSON → API Response
2. **Trade History** → JSON → API Response
3. **Error Messages** → Structured logging → API Error Response
4. **Progress Updates** → JSON → API Status Response

## Configuration Structures

### SimulationConfig
```cpp
struct SimulationConfig {
    std::vector<std::string> symbols;  // Supports single or multiple symbols
    std::string start_date;           // YYYY-MM-DD format
    std::string end_date;             // YYYY-MM-DD format
    double capital;                   // Starting capital amount
    std::string strategy;             // Strategy name
    std::map<std::string, double> strategy_parameters;  // Strategy parameters
    
    // Helper methods for parameter access
    int getIntParameter(const std::string& key, int default_value = 0) const;
    double getDoubleParameter(const std::string& key, double default_value = 0.0) const;
    void setParameter(const std::string& key, double value);
};
```

### BacktestConfig
```cpp
struct BacktestConfig {
    std::string symbol;
    std::string start_date;
    std::string end_date;
    double starting_capital;
    std::string strategy_name;
    StrategyConfig strategy_config;
};
```

### StrategyConfig
```cpp
struct StrategyConfig {
    std::map<std::string, double> parameters;
    double max_position_size = 0.1;              // Maximum position size as portfolio fraction
    double stop_loss_pct = -0.05;                // Stop loss percentage
    double take_profit_pct = 0.15;               // Take profit percentage
    bool enable_risk_management = true;           // Enable risk management features
    bool allow_position_increases = true;        // Allow position size increases
    double max_position_percentage = 0.3;        // Maximum position as portfolio percentage
    double position_increase_size = 0.05;        // Size of position increases
    int max_position_increases = 3;              // Maximum number of position increases
    bool enable_rebalancing = false;             // Enable portfolio rebalancing
    double rebalancing_threshold = 0.05;         // Rebalancing trigger threshold
    int rebalancing_frequency = 30;              // Rebalancing frequency in days
    
    // Parameter access methods
    void setParameter(const std::string& key, double value);
    double getParameter(const std::string& key, double default_value = 0.0) const;
    
    // Example usage:
    // For MA Crossover: 
    //   config.setParameter("short_period", 10); 
    //   config.setParameter("long_period", 20);
    // Or directly: config.parameters["short_period"] = 10.0;
    // For RSI: 
    //   config.setParameter("rsi_period", 14); 
    //   config.setParameter("oversold_threshold", 30);
};
```

## Performance Metrics Output

### BacktestResult
```cpp
struct BacktestResult {
    std::string symbol;                          // Symbol backtested
    double starting_capital;                     // Initial capital
    double ending_value;                         // Final portfolio value
    double total_return_pct;                     // Total return percentage
    int total_trades;                            // Total number of trades executed
    int winning_trades;                          // Number of profitable trades
    int losing_trades;                           // Number of losing trades
    double win_rate;                             // Percentage of winning trades
    double max_drawdown;                         // Maximum drawdown percentage
    double sharpe_ratio;                         // Risk-adjusted return metric
    std::vector<TradingSignal> signals_generated; // All generated trading signals
    std::vector<double> equity_curve;            // Portfolio value over time
    std::string start_date;                      // Backtest start date
    std::string end_date;                        // Backtest end date
    std::string error_message;                   // Error message if failed
};
```

### TradingSignal Structure
```cpp
enum class Signal {
    BUY,
    SELL,
    HOLD
};

struct TradingSignal {
    Signal signal;      // Trading signal type (BUY/SELL/HOLD)
    double price;       // Price at which signal was generated
    std::string date;   // Signal generation date (YYYY-MM-DD)
    std::string reason; // Reason for signal generation
    double confidence;  // Signal confidence level (0.0 to 1.0)
};
```

### PriceData Structure
```cpp
struct PriceData {
    double open;        // Opening price
    double high;        // High price
    double low;         // Low price
    double close;       // Closing price
    long volume;        // Trading volume
    std::string date;   // Date (YYYY-MM-DD)
};
```

## Error Handling

### Error Categories
- **VALIDATION_ERROR**: Invalid input parameters or configuration
- **DATABASE_ERROR**: Database connectivity or query failures
- **STRATEGY_ERROR**: Strategy initialisation or execution failures
- **PORTFOLIO_ERROR**: Insufficient funds or invalid positions
- **SYSTEM_ERROR**: General system or resource errors

### Error Response Format
```cpp
struct ErrorResponse {
    std::string error_code;     // Standardised error code
    std::string message;        // Human-readable error message
    std::string component;      // Component where error occurred
    std::string details;        // Additional error context
    std::string timestamp;      // Error occurrence time
};
```

## Command Line Interface

### Basic Usage
```bash
# Single symbol simulation
./trading_engine --simulate --symbol AAPL --start-date 2023-01-01 --end-date 2023-12-31 --capital 10000 --strategy ma_crossover

# Multi-symbol backtest
 ./trading_engine --backtest --config config.json

# Database connectivity test
./trading_engine --test-db

# Engine status check
./trading_engine --status
```

### JSON Configuration Example
```json
{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
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

## Dependencies and Requirements

### System Dependencies
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Compiler**: GCC 9+ or Clang 10+ with C++17 support
- **Database**: PostgreSQL 12+ with TimescaleDB extension
- **Build Tools**: CMake 3.16+, Make

### C++ Libraries
- **nlohmann/json**: JSON processing and serialisation
- **libpq**: PostgreSQL client library
- **pthread**: Multi-threading support (system library)

### Build Commands
```bash
# Install dependencies (Ubuntu)
sudo apt-get install build-essential cmake libpq-dev nlohmann-json3-dev

# Build engine
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run tests
./engine_tests

# Install (optional)
sudo make install
```

## Dynamic Temporal Validation

### Overview
The engine implements a dynamic temporal validation system that eliminates survivorship bias by ensuring stocks are only traded when they were actually available in the market. This approach provides backtesting results that accurately reflect historical market conditions.

#### Real-time Temporal Validation
```cpp
// During daily trading loop in trading_engine.cpp
for (const auto& [symbol, data] : multi_symbol_data) {
    // Check if stock is tradeable on current date
    auto is_tradeable = db_connection->checkStockTradeable(symbol, current_date);
    if (!is_tradeable.getValue()) {
        // Handle non-tradeable stocks appropriately
        continue;
    }
    // Only evaluate strategy for tradeable stocks
    TradingSignal signal = strategy_->evaluateSignal(historical_windows[symbol], portfolio_, symbol);
}
```

#### Automatic Position Management
- **IPO Handling**: Stocks ignored until their actual IPO date, then strategy evaluation begins
- **Delisting Handling**: Positions automatically liquidated when stocks become non-tradeable
- **Real-time Updates**: Database functions provide current trading status for each date

### Database Integration

#### Temporal Validation Functions
- `is_stock_tradeable(symbol, date)`: Returns boolean for specific date tradeability
- `get_eligible_stocks_for_period(start_date, end_date)`: Batch eligibility checking

#### Data Requirements
- **IPO Dates**: When stocks became publicly tradeable
- **Delisting Dates**: When stocks stopped trading (if applicable)
- **Trading Status**: Current status (active, delisted, suspended)
- **Exchange Information**: Listing and delisting context

## Integration with API

The C++ engine integrates with the Python API through:

1. **Command Line Interface**: API spawns engine processes with JSON configurations
2. **JSON Communication**: All input/output uses structured JSON format
3. **Progress Reporting**: Real-time progress updates via JSON status files
4. **Error Handling**: Standardised error codes and messages
5. **Result Processing**: Structured performance metrics and trade history

### API Integration Points
- **Simulation Execution**: `/simulation/start` endpoint spawns engine process
- **Status Monitoring**: Engine writes progress to temporary JSON files
- **Result Retrieval**: Engine output JSON parsed by API for client response
- **Error Propagation**: Engine error codes mapped to API error responses

## Notes

- All timestamps use ISO 8601 format (YYYY-MM-DD) for consistency
- Database connections use connection pooling for performance
- Memory usage optimised for large-scale backtesting (multi-year, multi-symbol)
- Error handling follows Result<T> pattern to avoid exceptions in hot paths
- Logging configured for both development debugging and production monitoring
- Thread-safe design enables concurrent simulation execution
- Modular architecture supports easy testing and component replacement
- Dynamic temporal validation eliminates survivorship bias through real-time IPO/delisting checking
- Survivorship bias mitigation ensures realistic backtesting results
