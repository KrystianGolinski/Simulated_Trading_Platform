# API Structure Documentation

## Standard Response Format

All endpoints return responses following this structure:

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

### Paginated Responses

Endpoints with pagination include additional structure:

```json
{
  "status": "success",
  "data": [array of items],
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

## Health Endpoints

### `GET /`
Root service information
- **Data**: `{"service": "Trading Platform API", "version": "1.0.0"}`

### `GET /health`
Complete system health check
- **Data**: Database status, C++ engine status, system resources

### `GET /health/ready`
Kubernetes readiness probe
- **Data**: `{"ready": boolean, "database": "status"}`

### `GET /health/live`
Kubernetes liveness probe
- **Data**: `{"alive": true, "timestamp": number}`

### `GET /health/dashboard`
Health dashboard with comprehensive metrics
- **Data**: Service info, health endpoints, monitoring configuration, and current health status

## Stock Data Endpoints

### `GET /stocks`
Get paginated list of stock symbols
- **Parameters**: `page` (1), `page_size` (100, max 1000)
- **Data**: Array of stock symbol strings

### `GET /stocks/{symbol}/date-range`
Get available date range for stock
- **Parameters**: `symbol` (path)
- **Data**: `{"min_date": "YYYY-MM-DD", "max_date": "YYYY-MM-DD"}`

### `GET /stocks/{symbol}/data`
Get historical stock data with pagination
- **Parameters**: 
  - `symbol` (path)
  - `start_date`, `end_date` (query, YYYY-MM-DD)
  - `timeframe` (query, default "daily")
  - `page` (1), `page_size` (1000, max 10000)
- **Data**: Array of OHLCV data objects

## Stock Temporal Validation Endpoints (Survivorship Bias Mitigation)

### `POST /stocks/validate-temporal`
Validate if stocks were trading during specified period (accounts for IPO dates, delisting dates)
- **Body**: 
```json
{
  "symbols": ["AAPL", "GOOGL", "UBER"],
  "start_date": "2020-01-01",
  "end_date": "2023-12-31"
}
```
- **Data**: 
```json
{
  "valid_symbols": ["AAPL", "GOOGL"],
  "rejected_symbols": ["UBER"],
  "errors": ["Stock UBER was not tradeable on 2020-01-01 (IPO date: 2019-05-10)"],
  "total_requested": 3,
  "total_valid": 2,
  "total_rejected": 1
}
```

### `GET /stocks/{symbol}/temporal-info`
Get temporal information for a stock (IPO, delisting, trading periods)
- **Parameters**: `symbol` (path)
- **Data**: 
```json
{
  "symbol": "AAPL",
  "ipo_date": "1980-12-12",
  "listing_date": "1980-12-12", 
  "delisting_date": null,
  "trading_status": "active",
  "exchange_status": "listed",
  "first_trading_date": "1980-12-12",
  "last_trading_date": null
}
```

### `POST /stocks/check-tradeable`
Check if a stock was tradeable on a specific date
- **Body**:
```json
{
  "symbol": "UBER",
  "check_date": "2018-01-01"
}
```
- **Data**:
```json
{
  "symbol": "UBER",
  "check_date": "2018-01-01",
  "is_tradeable": false,
  "temporal_context": {
    "ipo_date": "2019-05-10",
    "listing_date": "2019-05-10",
    "delisting_date": null,
    "trading_status": "active"
  }
}
```

### `GET /stocks/eligible-for-period`
Get stocks that were eligible for trading during a specific period
- **Parameters**: `start_date`, `end_date` (query, YYYY-MM-DD)
- **Data**: Array of eligible stock symbols that were tradeable during the entire period

## Simulation Endpoints

### `POST /simulation/validate`
Validate simulation configuration
- **Body**: `SimulationConfig` object
- **Data**: `{"is_valid": boolean, "errors": [...], "warnings": [...]}`

### `POST /simulation/start`
Start new simulation
- **Body**: `SimulationConfig` object
- **Data**: `{"simulation_id": "uuid", "status": "pending", "message": "..."}`

### `GET /simulation/{simulation_id}/status`
Get simulation status
- **Data**: 
```json
{
  "simulation_id": "uuid",
  "status": "pending|running|completed|failed",
  "progress_pct": number,
  "current_date": "YYYY-MM-DD",
  "elapsed_time": number,
  "estimated_remaining": number
}
```

### `GET /simulation/{simulation_id}/results`
Get complete simulation results
- **Data**: `SimulationResults` with performance metrics, trades, equity curve

### `GET /simulation/{simulation_id}/cancel`
Cancel running simulation
- **Data**: `{"status": "cancelled"}`

### `GET /simulations`
List all simulations
- **Data**: `{simulation_id: SimulationResults}` mapping

## Strategy Endpoints

### `GET /strategies`
Get all available strategies
- **Data**: Strategy metadata from registry

### `GET /strategies/{strategy_id}`
Get specific strategy details
- **Data**: Strategy parameters and requirements

### `POST /strategies/{strategy_id}/validate`
Validate strategy parameters
- **Body**: `{"parameters": {...}}`
- **Data**: Validation status

### `POST /strategies/refresh`
Refresh strategy registry to discover new strategies
- **Data**: Information about newly discovered strategies

### `GET /strategies/categories`
Get strategy categories for filtering and organisation
- **Data**: `{"categories": [{"name": "string", "strategies": [...], "count": number}]}`

## Performance Endpoints

### `GET /performance/stats`
System performance statistics
- **Data**: Optimisation and database metrics

### `POST /performance/clear-cache`
Clear performance caches
- **Data**: `{"cache_status": "cleared"}`

### `GET /performance/cache-stats`
Get cache performance statistics
- **Data**: `{"optimizer_cache": {}, "database_cache": {}, "timestamp": "ISO date"}`

## Engine Endpoints

### `GET /engine/test`
Test C++ engine directly
- **Data**: `{"command": "string", "return_code": number, "stdout": "string"}`

### `GET /engine/status`
Get engine status and path information
- **Data**: Engine availability and directory information

## Key Data Models

### SimulationConfig
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

### PerformanceMetrics
```json
{
  "total_return_pct": 15.5,
  "sharpe_ratio": 1.2,
  "max_drawdown_pct": -8.5,
  "win_rate": 0.65,
  "total_trades": 45,
  "winning_trades": 29,
  "losing_trades": 16,
  "final_balance": 11550.0,
  "starting_capital": 10000.0,
  "max_drawdown": -850.0,
  "profit_factor": 2.1,
  "average_win": 85.75,
  "average_loss": -62.30,
  "annualized_return": 12.8,
  "volatility": 18.5,
  "signals_generated": 52
}
```

### TradeRecord
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

## Error Codes

### General Error Codes
- `VALIDATION_FAILED`: Input validation errors
- `SIMULATION_NOT_FOUND`: Simulation ID not found
- `ENGINE_NOT_FOUND`: C++ engine unavailable
- `SYMBOL_NOT_FOUND`: Stock symbol not in database
- `STRATEGY_INVALID`: Invalid strategy configuration
- `INTERNAL_ERROR`: General system errors

### Temporal Validation Error Codes
- `STOCK_NOT_YET_PUBLIC`: Stock was not tradeable on requested date (before IPO)
- `STOCK_DELISTED`: Stock was not tradeable on requested date (after delisting)
- `INVALID_DATE_RANGE`: Start date is after end date
- `INVALID_DATE_FORMAT`: Date format is not YYYY-MM-DD
- `TEMPORAL_VALIDATION_ERROR`: General temporal validation failure

## Notes

- All endpoints use standardised response format with proper HTTP status codes
- Comprehensive validation through Pydantic models and business logic validators
- Temporal validation ensures stocks are only included when they were actually tradeable
- Pagination available on data-heavy endpoints with configurable limits
- Error responses include detailed field-level validation information
- CORS headers configured for frontend integration
- Enhanced simulation validation now includes IPO/delisting date checking