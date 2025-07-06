# API Technical Documentation

## 1. Introduction

This document provides a technical overview of the FastAPI-based API for the Simulated Trading Platform. It is intended for developers working on maintaining or extending the API's functionality. The focus is on architecture, conventions, and practical guides for common development tasks.

### 1.1. Core Design Principles

The API is built on a set of core principles to ensure consistency, maintainability, and scalability:

-   **Layered Architecture**: A clear separation of concerns between presentation, business logic, data access, and database layers.
-   **Dependency Injection**: FastAPI's DI system is used to manage dependencies and decouple components, particularly for injecting services and repositories into the API routers.
-   **Standardized I/O**: All API endpoints use a consistent JSON structure for requests and responses, including a standardized format for errors and pagination.
-   **Configuration-driven**: Key behaviors are managed through configuration, not hard-coded.
-   **Extensibility**: The architecture is designed to be extensible, particularly for adding new trading strategies and API endpoints.

### 1.2. Key Directory Mapping

#### Core API Structure
-   `Backend/api/routers/`: API Endpoint definitions (the "API Layer").
    -   `health.py`: Health check endpoints.
    -   `simulation.py`: Simulation lifecycle management.
    -   `stocks.py`: Stock data and temporal validation.
    -   `strategies.py`: Strategy management.
    -   `engine.py`: C++ engine interface.
    -   `performance.py`: Performance analytics.
-   `Backend/api/services/`: Core business logic.
    -   `equity_processor.py`: Equity processing logic.
    -   `error_categorizers.py`: Error categorization.
    -   `error_handler.py`: Centralized error handling.
    -   `error_types.py`: Error type definitions.
    -   `execution_service.py`: Trade execution logic.
    -   `performance_calculator.py`: Performance metrics calculation.
    -   `result_processor.py`: Result processing and aggregation.
    -   `strategy_service.py`: Strategy interface.
    -   `strategy_service_implementation.py`: Strategy service implementation.
    -   `temporal_validation_service.py`: Temporal validation logic.
    -   `trade_converter.py`: Trade data conversion.
-   `Backend/api/repositories/`: Data access logic (the "Repository Layer").
    -   `stock_data_repository.py`: Stock data access.
-   `Backend/api/models.py`: Pydantic models for request/response validation and standardised API responses.
-   `Backend/api/dependencies.py`: Service and repository dependency injector functions.
-   `Backend/api/routing/`: Core router implementation (`RouterBase`).
    -   `router_base.py`: Base router class.
    -   `service_factory.py`: Service factory for router creation.
-   `Backend/api/api_components/`: Shared infrastructure (logging, response formatting, validation).
    -   `response_formatter.py`: Response formatting utilities.
    -   `router_logger.py`: Router-specific logging.
    -   `validation_service.py`: Validation utilities.
-   `Backend/api/db_components/`: Low-level database interaction components.
    -   `cache_manager.py`: In-memory caching.
    -   `connection_manager.py`: Database connection management.
    -   `query_executor.py`: Query execution utilities.
-   `Backend/api/strategies/`: Core trading strategy implementations.
-   `Backend/api/plugins/strategies/`: Discoverable trading strategy plugins.
-   `Backend/api/strategy_registry.py`: Dynamic strategy registration and discovery system.
-   `Backend/api/strategy_factory.py`: Strategy instantiation and configuration management.
-   `Backend/api/simulation_engine.py`: Simulation orchestration and C++ engine integration.
-   `Backend/api/performance_optimizer.py`: Performance optimizations and execution analytics.
-   `Backend/api/database.py`: Database connection management.
-   `Backend/api/validation.py`: Global validation utilities.
-   `Backend/api/main.py`: FastAPI application entry point.
-   `Backend/api/tests/`: Comprehensive test suite.

## 2. Architecture

The API follows a layered architecture, as illustrated in the diagram below.

### 2.1. Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                HTTP Requests                                    │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                        API Layer (RouterBase Pattern)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  stocks.py      │  │ simulation.py   │  │   health.py     │                  │
│  │  /stocks/*      │  │ /simulation/*   │  │   /health/*     │                  │
│  │ (RouterBase)    │  │ (RouterBase)    │  │ (RouterBase)    │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ strategies.py   │  │  engine.py      │  │ performance.py  │                  │
│  │ /strategies/*   │  │  /engine/*      │  │ /performance/*  │                  │
│  │ (RouterBase)    │  │ (RouterBase)    │  │ (RouterBase)    │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ Service Injection
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                    Routing Infrastructure Layer                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                    RouterServiceFactory                                     ││
│  │  • RouterBase creation with service injection                               ││
│  │  • Singleton management for shared services                                 ││
│  │  • Per-router logger instances                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                   Infrastructure Services Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ValidationService│  │ResponseFormatter│  │  RouterLogger   │                  │
│  │                 │  │                 │  │                 │                  │
│  │• validate_with_ │  │• create_success │  │• log_request()  │                  │
│  │  service()      │  │  _response()    │  │• log_success()  │                  │
│  │• create_errors()│  │• format_pagina- │  │• log_error()    │                  │
│  │• log_warnings() │  │  ted_response() │  │• correlation_id │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ Business Logic Dependencies
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                     Dependencies Layer                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                    dependencies.py                                          ││
│  │  • get_stock_data_repository()                                              ││
│  │  • get_temporal_validation_service()                                        ││
│  │  • get_simulation_validator()                                               ││
│  │  • get_database()                                                           ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                                            │
│  ┌───────────────────┐       ┌──────────────────┐           ┌───────────────────┐    │
│  │StockDataRepository│       │TemporalValidation│           │SimulationValidator│    │
│  │                   │       │    Service       │           │                   │    │
│  │• get_stocks()     │       │• is_tradeable()  │           │• validate_config  │    │
│  │• get_prices()     │       │• validate_period │           │• check_symbols    │    │
│  │• validate_symbol  │       │• get_eligible()  │           │• aggregate_errors │    │
│  └───────────────────┘       └──────────────────┘           └───────────────────┘    │
│                                                                                      │
│  ┌───────────────────┐       ┌──────────────────────┐       ┌────────────────────┐   │
│  │ StrategyRegistry  │       │ SimulationEngine     │       │PerformanceOptimizer│   │
│  │                   │       │                      │       │                    │   │
│  │• register_strategy│       │• start_simulation    │       │• analyze_complexity│   │
│  │• discover_plugins │       │• parallel_tracking   │       │• execute_parallel  │   │
│  │• validate_configs │       │• progress_aggregation│       │• group_optimization│   │
│  └───────────────────┘       └──────────────────────┘       └────────────────────┘   │
│                                                                                      │
│  ┌───────────────────┐       ┌──────────────────┐           ┌─────────────────────┐  │
│  │ ExecutionService  │       │StrategyService   │           │PerformanceCalculator│  │
│  │                   │       │                  │           │                     │  │
│  │• execute_trades() │       │• validate_params │           │• calculate_metrics  │  │
│  │• manage_orders()  │       │• create_strategy │           │• compute_returns    │  │
│  │• position_mgmt()  │       │• execute_signals │           │• risk_analysis      │  │
│  └───────────────────┘       └──────────────────┘           └─────────────────────┘  │
│                                                                                      │
│  ┌───────────────────┐       ┌──────────────────┐           ┌────────────────────┐   │
│  │ ErrorHandler      │       │ ResultProcessor  │           │ TradeConverter     │   │
│  │                   │       │                  │           │                    │   │
│  │• categorize_error │       │• process_results │           │• convert_trades    │   │
│  │• handle_exception │       │• aggregate_data  │           │• format_output     │   │
│  │• log_errors       │       │• validate_output │           │• validate_trades   │   │
│  └───────────────────┘       └──────────────────┘           └────────────────────┘   │
└─────────────────────────┬────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                    Database Layer                                               │
│  ┌──────────────────┐        ┌─────────────────┐        ┌─────────────────┐     │
│  │DatabaseConnection│        │  QueryExecutor  │        │  CacheManager   │     │
│  │    Manager       │        │                 │        │                 │     │
│  │• create_pool()   │        │• execute_query()│        │• get_cached()   │     │
│  │• get_connection  │        │• execute_single │        │• set_cache()    │     │
│  │• health_check()  │        │• transactions   │        │• invalidate()   │     │
│  └──────────────────┘        └─────────────────┘        └─────────────────┘     │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                          Database - TimescaleDB                                 │
│                                                                                 │
│  ┌─────────────────┐     ┌──────────────────┐         ┌─────────────────┐       │
│  │     stocks      │     │stock_prices_daily│         │trading_sessions │       │
│  │   (metadata)    │     │   (OHLCV data)   │         │   (sessions)    │       │
│  └─────────────────┘     └──────────────────┘         └─────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2. Data Flow Example: Parallel Simulation Execution

1.  **HTTP Request**: `POST /simulation/start` arrives with simulation configuration.
2.  **API Layer**: Request routed to `routers/simulation.py` with validation via `SimulationValidator`.
3.  **Complexity Analysis**: `PerformanceOptimizer` analyzes symbols count, date range, and strategy complexity.
4.  **Strategy Selection**: System chooses sequential or parallel execution based on complexity score.
5.  **Parallel Execution** (if selected):
    - Symbols grouped into balanced sets using `ParallelExecutionStrategy`
    - Multiple `ExecutionService` instances execute groups concurrently
    - Each group reports progress via C++ engine stderr JSON streams
6.  **Progress Aggregation**: `SimulationEngine` aggregates real-time progress from all parallel groups.
7.  **Result Processing**: Completed groups' results combined via `_aggregate_parallel_results()`.
8.  **Response**: Unified simulation results returned with optimization metadata.

## 3. API Reference

### 3.1. Standard Response Formats

**Standard Success/Error Response**
```json
{
  "status": "success|error|warning",
  "message": "Response message",
  "data": null|object|array,
  "errors": [
    {
      "code": "ERROR_CODE",
      "message": "Error description",
      "field": "field_name",
      "details": {}
    }
  ],
  "warnings": ["warning messages"],
  "metadata": {}
}
```

**Paginated Response**
```json
{
  "status": "success",
  "data": "[...items]",
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_count": 1000,
    "total_pages": 10,
    "has_next": true,
    "has_previous": false
  }
}
```

### 3.2. Key Data Models

**SimulationConfig**
```json
{
  "symbols": ["AAPL", "GOOGL"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "starting_capital": 10000.0,
  "strategy": "ma_crossover",
  "strategy_parameters": {}
}
```

**PerformanceMetrics**
```json
{
  "total_return_pct": 15.5,
  "sharpe_ratio": 1.2,
  "max_drawdown_pct": -8.5,
  "win_rate": 0.65,
  "total_trades": 45,
  "final_balance": 11550.0
}
```

**TradeRecord**
```json
{
  "date": "2023-06-15",
  "symbol": "AAPL",
  "action": "BUY",
  "shares": 10,
  "price": 185.50,
  "total_value": 1855.0
}
```

### 3.3. Error Codes

-   `VALIDATION_FAILED`: Input validation errors.
-   `SIMULATION_NOT_FOUND`: Simulation ID not found.
-   `ENGINE_NOT_FOUND`: C++ engine unavailable.
-   `SYMBOL_NOT_FOUND`: Stock symbol not in database.
-   `STRATEGY_INVALID`: Invalid strategy configuration.
-   `STOCK_NOT_YET_PUBLIC`: Stock was not tradeable on the requested date (before IPO).
-   `STOCK_DELISTED`: Stock was not tradeable on the requested date (after delisting).
-   `INTERNAL_ERROR`: General system errors.

### 3.4. Endpoints

#### Health
-   `GET /`: Root service information.
-   `GET /health`: Complete system health check (DB, C++ engine, etc.).
-   `GET /health/ready`: Kubernetes readiness probe.
-   `GET /health/live`: Kubernetes liveness probe.
-   `GET /health/dashboard`: Health dashboard with detailed metrics.

#### Stock Data
-   `GET /stocks`: Get a paginated list of all stock symbols.
-   `GET /stocks/{symbol}/date-range`: Get the available date range for a stock.
-   `GET /stocks/{symbol}/data`: Get historical OHLCV data for a stock.

#### Temporal Validation
-   `POST /stocks/validate-temporal`: Validate if a list of stocks were trading during a specified period.
-   `GET /stocks/{symbol}/temporal-info`: Get temporal information for a stock (IPO, delisting dates).
-   `POST /stocks/check-tradeable`: Check if a stock was tradeable on a specific date.
-   `GET /stocks/eligible-for-period`: Get stocks that were tradeable during an entire period.

#### Simulation
-   `POST /simulation/validate`: Validate a simulation configuration without running it.
-   `POST /simulation/start`: Start a new simulation with automatic optimization.
-   `GET /simulation/{simulation_id}/status`: Get real-time status and aggregated progress (sequential/parallel).
-   `GET /simulation/{simulation_id}/results`: Get complete results with optimization metadata.
-   `GET /simulation/{simulation_id}/cancel`: Cancel a running simulation (supports parallel cancellation).
-   `GET /simulations`: List all historical simulations with performance metrics.

#### Strategy
-   `GET /strategies`: Get all available, discovered strategies.
-   `GET /strategies/{strategy_id}`: Get details and required parameters for a specific strategy.
-   `POST /strategies/{strategy_id}/validate`: Validate a set of parameters for a given strategy.
-   `POST /strategies/refresh`: Force the system to rediscover and reload all strategy plugins.
-   `GET /strategies/categories`: Get strategy categories for filtering.

#### Performance & Engine
-   `GET /performance/stats`: Parallel execution metrics and optimization analytics.
-   `POST /performance/clear-cache`: Clear all system caches.
-   `GET /performance/cache-stats`: Cache performance and hit rates.
-   `GET /engine/test`: Test C++ engine connection and parallel execution capability.
-   `GET /engine/status`: Engine status with worker availability and resource usage.