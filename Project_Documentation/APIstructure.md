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

-   `Backend/api/routers/`: API Endpoint definitions (the "API Layer").
-   `Backend/api/services/`: Core business logic.
-   `Backend/api/repositories/`: Data access logic (the "Repository Layer").
-   `Backend/api/models.py`: Pydantic models for request/response validation and standardised API responses.
-   `Backend/api/dependencies.py`: Service and repository dependency injector functions.
-   `Backend/api/routing/`: Core router implementation (`RouterBase`).
-   `Backend/api/api_components/`: Shared infrastructure (logging, response formatting, validation).
-   `Backend/api/db_components/`: Low-level database interaction components.
-   `Backend/api/strategies/`: Core trading strategy implementations.
-   `Backend/api/plugins/strategies/`: Discoverable trading strategy plugins.
-   `Backend/api/strategy_registry.py`: Dynamic strategy registration and discovery system.
-   `Backend/api/strategy_factory.py`: Strategy instantiation and configuration management.
-   `Backend/api/simulation_engine.py`: Simulation orchestration and C++ engine integration.
-   `Backend/api/performance_optimizer.py`: Performance optimizations and execution analytics.

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
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                      Business Logic Layer                                       │
│  ┌───────────────────┐       ┌──────────────────┐       ┌───────────────────┐   │
│  │StockDataRepository│       │TemporalValidation│       │SimulationValidator│   │
│  │                   │       │    Service       │       │                   │   │
│  │• get_stocks()     │       │• is_tradeable()  │       │• validate_config  │   │
│  │• get_prices()     │       │• validate_period │       │• check_symbols    │   │
│  │• validate_symbol  │       │• get_eligible()  │       │• aggregate_errors │   │
│  └───────────────────┘       └──────────────────┘       └───────────────────┘   │
│                                                                                 │
│  ┌───────────────────┐       ┌──────────────────┐       ┌────────────────────┐  │
│  │ StrategyRegistry  │       │ SimulationEngine │       │PerformanceOptimizer│  │
│  │                   │       │                  │       │                    │  │
│  │• register_strategy│       │• start_simulation│       │• optimize_config   │  │
│  │• discover_plugins │       │• orchestrate_runs│       │• track_metrics     │  │
│  │• validate_configs │       │• process_results │       │• cache_management  │  │
│  └───────────────────┘       └──────────────────┘       └────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────────────────────┘
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

### 2.2. Data Flow Example: Stock Data Request

1.  **HTTP Request**: `GET /stocks/{symbol}/data` arrives at the FastAPI application.
2.  **API Layer**: The request is routed to the appropriate endpoint in `routers/stocks.py`. This router is an instance of `RouterBase`.
3.  **Logging**: `RouterLogger` logs the incoming request with a unique correlation ID.
4.  **Dependency Injection**: FastAPI injects the `StockDataRepository` into the endpoint function by calling `get_stock_data_repository()` from `dependencies.py`.
5.  **Repository Layer**: The endpoint calls `StockDataRepository.get_stock_prices()`.
6.  **Database Layer**: The repository uses `QueryExecutor` to execute the SQL query against the TimescaleDB. Caching is checked via `CacheManager`.
7.  **Response Formatting**: The data is returned to the router, which uses the injected `ResponseFormatter` to construct a standard, paginated JSON response.
8.  **Logging**: `RouterLogger` logs the successful response before it is sent to the client.

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
-   `POST /simulation/start`: Start a new simulation.
-   `GET /simulation/{simulation_id}/status`: Get the status and progress of a running simulation.
-   `GET /simulation/{simulation_id}/results`: Get the complete results of a finished simulation.
-   `GET /simulation/{simulation_id}/cancel`: Cancel a running simulation.
-   `GET /simulations`: List all historical simulations.

#### Strategy
-   `GET /strategies`: Get all available, discovered strategies.
-   `GET /strategies/{strategy_id}`: Get details and required parameters for a specific strategy.
-   `POST /strategies/{strategy_id}/validate`: Validate a set of parameters for a given strategy.
-   `POST /strategies/refresh`: Force the system to rediscover and reload all strategy plugins.
-   `GET /strategies/categories`: Get strategy categories for filtering.

#### Performance & Engine
-   `GET /performance/stats`: System performance and cache metrics.
-   `POST /performance/clear-cache`: Clear all system caches.
-   `GET /performance/cache-stats`: Get detailed cache performance statistics.
-   `GET /engine/test`: Directly test the C++ engine connection.
-   `GET /engine/status`: Get the status and path information for the C++ engine.