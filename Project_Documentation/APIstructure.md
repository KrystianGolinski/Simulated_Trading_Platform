# API Technical Documentation

## 1. Introduction

This document provides a technical overview of the FastAPI-based API for the Simulated Trading Platform. It is intended for developers working on maintaining or extending the API's functionality. The focus is on architecture, conventions, and practical guides for common development tasks.

**Current Version:** 1.0.0  
**Framework:** FastAPI with Python 3.12  
**Container:** Docker with health checks and dependency management  
**Database Integration:** Async PostgreSQL/TimescaleDB via asyncpg

### 1.1. Core Design Principles

The API is built on a set of core principles to ensure consistency, maintainability, and scalability:

-   **Layered Architecture**: A clear separation of concerns between presentation, business logic, data access, and database layers.
-   **Dependency Injection**: FastAPI's DI system is used to manage dependencies and decouple components, particularly for injecting services and repositories into the API routers.
-   **Standardized I/O**: All API endpoints use a consistent JSON structure for requests and responses, including a standardized format for errors and pagination.
-   **RouterBase Pattern**: All routers inherit from a common base pattern providing consistent logging, response formatting, and error handling.
-   **Correlation ID Support**: Each request is tracked with a unique correlation ID for distributed tracing across components.
-   **Configuration-driven**: Key behaviors are managed through configuration, not hard-coded.
-   **Extensibility**: The architecture is designed to be extensible, particularly for adding new trading strategies and API endpoints through plugin discovery.
-   **Global Exception Handling**: Unified exception handling with standardized error responses across all endpoints.

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

The API follows a layered architecture with FastAPI at its core, implementing the RouterBase pattern for consistent endpoint management. The system emphasizes dependency injection, standardized response formatting, and comprehensive error handling.

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

### 2.2. Request Processing Flow

1.  **Request Reception**: FastAPI receives HTTP request with correlation ID middleware
2.  **CORS Processing**: Cross-origin validation for frontend requests
3.  **Router Dispatch**: Request routed to appropriate router using RouterBase pattern
4.  **Dependency Injection**: Services and repositories injected via FastAPI DI system
5.  **Validation**: Request validated using Pydantic models and custom validators
6.  **Business Logic**: RouterBase delegates to appropriate service layer
7.  **Error Handling**: Global exception handlers catch and format errors
8.  **Response Formatting**: Standardized response format with metadata
9.  **Correlation Tracking**: Response includes correlation ID for request tracing
10. **Logging**: Request/response logged with correlation ID for monitoring

### 2.3. Simulation Processing Flow

1.  **Configuration Validation**: `SimulationValidator` validates symbols, dates, and strategy
2.  **Strategy Discovery**: Dynamic strategy loading from core and plugin registries
3.  **Optimization Analysis**: `PerformanceOptimizer` determines execution strategy
4.  **Engine Coordination**: `SimulationEngine` orchestrates C++ engine execution
5.  **Progress Tracking**: Real-time progress updates via JSON streams
6.  **Result Processing**: Performance metrics calculation and result aggregation
7.  **Response Generation**: Standardized simulation response with metadata

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
  "metadata": {
    "correlation_id": "uuid",
    "timestamp": "iso_datetime",
    "execution_time_ms": 150
  }
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

#### Validation Errors
-   `VALIDATION_FAILED`: General input validation failures
-   `INVALID_INPUT`: Invalid parameter types or formats
-   `SYMBOL_NOT_FOUND`: Stock symbol not found in database
-   `STRATEGY_INVALID`: Invalid strategy configuration or parameters

#### Temporal Validation Errors
-   `STOCK_NOT_YET_PUBLIC`: Stock not tradeable before IPO date
-   `STOCK_DELISTED`: Stock not tradeable after delisting date
-   `DATE_RANGE_INVALID`: Invalid date range (future dates, end before start)

#### Simulation Errors
-   `SIMULATION_NOT_FOUND`: Simulation ID not found in system
-   `SIMULATION_FAILED`: Simulation execution failure
-   `ENGINE_NOT_FOUND`: C++ trading engine unavailable
-   `ENGINE_ERROR`: C++ engine execution error

#### System Errors
-   `OPERATION_ERROR`: Business logic operation failures
-   `INTERNAL_ERROR`: Unexpected system errors
-   `DATABASE_ERROR`: Database connectivity or query errors
-   `CACHE_ERROR`: Cache operation failures
-   `TIMEOUT_ERROR`: Request timeout or processing timeout
-   `RESOURCE_EXHAUSTED`: System resource limitations exceeded
-   `SERVICE_UNAVAILABLE`: Dependent service unavailable
-   `CONFIGURATION_ERROR`: System configuration issues

#### Strategy Errors
-   `STRATEGY_NOT_FOUND`: Specified strategy not available in registry
-   `STRATEGY_PARAMETER_INVALID`: Invalid or missing strategy parameters
-   `STRATEGY_EXECUTION_ERROR`: Error during strategy signal generation
-   `STRATEGY_PLUGIN_ERROR`: Plugin loading or validation failures

### 3.4. Current API Endpoints

#### Health Management
-   `GET /`: Root service information with API version and status.
-   `GET /health`: Complete system health check (DB, C++ engine, service status).
-   `GET /health/ready`: Kubernetes readiness probe for container orchestration.
-   `GET /health/live`: Kubernetes liveness probe for container management.
-   `GET /health/dashboard`: Health dashboard with detailed system metrics.

#### Stock Data & Temporal Validation
-   `GET /stocks`: Get paginated list of all available stock symbols with metadata.
-   `GET /stocks/{symbol}/date-range`: Get available historical date range for a stock.
-   `GET /stocks/{symbol}/data`: Get historical OHLCV data with optional date filtering.
-   `POST /stocks/validate-temporal`: Validate if stocks were trading during a period.
-   `GET /stocks/{symbol}/temporal-info`: Get IPO, delisting, and trading period information.
-   `POST /stocks/check-tradeable`: Check if a stock was tradeable on a specific date.
-   `GET /stocks/eligible-for-period`: Get stocks tradeable throughout entire period.

#### Simulation Management
-   `POST /simulation/validate`: Validate simulation configuration without execution.
-   `POST /simulation/start`: Start new simulation with automatic optimization selection.
-   `GET /simulation/{simulation_id}/status`: Get real-time status and progress tracking.
-   `GET /simulation/{simulation_id}/results`: Get complete results with performance metrics.
-   `GET /simulation/{simulation_id}/memory`: Get memory usage statistics and optimization data.
-   `POST /simulation/{simulation_id}/cancel`: Cancel running simulation (parallel support).
-   `GET /simulations`: List historical simulations with status and performance summary.

#### Trading Strategy Management
-   `GET /strategies`: Get all discovered strategies (core + plugins).
-   `GET /strategies/{strategy_id}`: Get strategy details and required parameters.
-   `POST /strategies/{strategy_id}/validate`: Validate strategy parameters.
-   `POST /strategies/refresh`: Force strategy plugin rediscovery.
-   `GET /strategies/categories`: Get strategy categories for filtering and organization.

#### Performance Analytics & Engine Interface
-   `GET /performance/stats`: System performance metrics and optimization analytics.
-   `POST /performance/clear-cache`: Clear all system and database caches.
-   `GET /performance/cache-stats`: Cache performance statistics and hit rates.
-   `GET /engine/test`: Test C++ trading engine connectivity and functionality.
-   `GET /engine/status`: Engine status with resource usage and availability.

### 3.5. Authentication

#### Current Authentication Status
- **Authentication Model**: No authentication required
- **Security Model**: Open access for development and demonstration
- **Request Validation**: Parameter validation without user authentication
- **Future Considerations**: JWT or API key authentication can be added via middleware

### 3.6. Simulation Endpoint Documentation

#### POST /simulation/start
**Parameters**:
- `symbols`: Array of stock symbols (required, 1-50 symbols)
- `start_date`: Start date in YYYY-MM-DD format (required)
- `end_date`: End date in YYYY-MM-DD format (required)
- `starting_capital`: Initial capital amount (required, min: 1000, max: 10000000)
- `strategy`: Strategy identifier (required, from available strategies)
- `strategy_parameters`: Strategy-specific configuration object (optional)

**Response**:
```json
{
  "status": "success",
  "data": {
    "simulation_id": "uuid-string",
    "status": "queued",
    "estimated_duration": "5m 30s"
  },
  "metadata": {
    "correlation_id": "request-uuid",
    "timestamp": "2024-01-15T14:30:00Z",
    "execution_time_ms": 245
  }
}
```

#### GET /simulation/{simulation_id}/status
**Parameters**:
- `simulation_id`: UUID of the simulation (path parameter)

**Response**:
```json
{
  "status": "success",
  "data": {
    "simulation_id": "uuid-string",
    "status": "running",
    "progress_pct": 67.5,
    "current_date": "2023-08-15",
    "estimated_remaining": "1m 45s",
    "trades_executed": 23,
    "current_balance": 10750.50
  }
}
```

### 3.7. Strategy Plugin Architecture

#### Plugin Discovery System
- **Core Strategies**: Built-in strategies in `Backend/api/strategies/`
- **Plugin Directory**: External strategies in `Backend/api/plugins/strategies/`
- **Dynamic Loading**: Automatic discovery and registration at startup
- **Validation**: Schema validation for plugin configuration files
- **Interface Compliance**: All strategies implement `TradingStrategy` base class

#### Strategy Registration Process
1. **File Discovery**: Scan plugin directories for Python modules
2. **Module Import**: Dynamic import with error handling
3. **Interface Validation**: Verify strategy implements required methods
4. **Parameter Schema**: Extract and validate parameter definitions
5. **Registry Addition**: Add to central strategy registry
6. **API Exposure**: Make available via `/strategies` endpoints

#### Plugin Configuration Format
```json
{
  "name": "custom_rsi_strategy",
  "display_name": "Custom RSI Strategy",
  "description": "RSI-based trading with custom thresholds",
  "version": "1.0.0",
  "author": "Strategy Developer",
  "parameters": {
    "rsi_period": {
      "type": "integer",
      "default": 14,
      "min": 5,
      "max": 50,
      "description": "RSI calculation period"
    },
    "oversold_threshold": {
      "type": "float",
      "default": 30.0,
      "min": 10.0,
      "max": 40.0
    }
  }
}
```

### 3.8. Global Features

#### CORS Configuration
- **Origins**: `http://localhost:3000` (React development server)
- **Credentials**: Enabled for authentication support
- **Methods**: All HTTP methods supported
- **Headers**: All headers including custom correlation ID headers

#### Correlation ID Tracking
- **Header**: `X-Correlation-ID` for request tracing
- **Generation**: Auto-generated UUID if not provided
- **Logging**: Integrated into all log messages for distributed debugging
- **Response**: Correlation ID returned in response headers

#### Response Metadata Structure
**Standard Metadata Fields**:
- `correlation_id`: Unique request identifier (UUID format)
- `timestamp`: ISO 8601 datetime of response generation
- `execution_time_ms`: Request processing time in milliseconds
- `api_version`: Current API version (e.g., "1.0.0")
- `request_id`: Internal request tracking ID

#### Exception Handling
- **ValidationError**: HTTP 400 with detailed validation errors
- **OperationError**: HTTP 500 for business logic failures
- **ValueError**: HTTP 400 for invalid input parameters
- **General Exception**: HTTP 500 with generic error message for security