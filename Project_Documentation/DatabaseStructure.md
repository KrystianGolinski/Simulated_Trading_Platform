# Database Structure Documentation

## Overview

Using TimescaleDB (PostgreSQL extension) as its primary database technology, specifically designed for time-series data handling. The database is deployed via Docker containers with health monitoring and connection pooling.

### Database Technology Stack
- **Database Engine**: TimescaleDB (latest-pg15) - PostgreSQL 15 with TimescaleDB extension
- **Connection Technology**: 
  - Python: AsyncPG with connection pooling
  - C++: libpq-fe (PostgreSQL C library)
- **Container**: Docker with persistent volumes
- **Connection Pooling**: 10-50 connections (configurable)

## Database Configuration

### Connection Parameters

#### Production/Docker Environment
```
Host: postgres (Docker service name)
Port: 5432 (internal container port)
Database: simulated_trading_platform
User: trading_user
Password: trading_password
External Port: 5433 (mapped from container)
```

#### Test Environment
```
Host: localhost
Port: 5433
Database: simulated_trading_platform
User: trading_user
Password: trading_password
```

### Environment Variables
```bash
# Docker Environment (C++ Engine)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=simulated_trading_platform
DB_USER=trading_user
DB_PASSWORD=trading_password

# Local Testing (Python API accessing Docker containers)
TEST_DB_HOST=localhost
TEST_DB_PORT=5433
TEST_DB_NAME=simulated_trading_platform
TEST_DB_USER=trading_user
TEST_DB_PASSWORD=trading_password

# Full Connection URL
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/simulated_trading_platform
```

## Database Schema

### Core Tables

#### 1. stocks (Metadata Table with Temporal Tracking)
**Purpose**: Stores metadata about available stock symbols with temporal tracking for survivorship bias mitigation

```sql
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(100),
    exchange VARCHAR(50),
    active BOOLEAN DEFAULT true,
    listing_date DATE,                    -- Date stock was first listed on exchange
    delisting_date DATE,                  -- Date stock was delisted (NULL if still active)
    ipo_date DATE,                        -- Initial Public Offering date
    trading_status VARCHAR(20) DEFAULT 'active',  -- Current trading status: active, suspended, delisted
    exchange_status VARCHAR(20) DEFAULT 'listed', -- Exchange status: listed, delisted, transferred
    first_trading_date DATE,              -- First date of actual trading data available
    last_trading_date DATE,               -- Last date of trading data (NULL if still trading)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns**:
- `symbol` (VARCHAR(10), PRIMARY KEY): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
- `name` (VARCHAR(255)): Full company name
- `sector` (VARCHAR(100)): Business sector classification
- `exchange` (VARCHAR(50)): Stock exchange (NYSE, NASDAQ, etc.)
- `active` (BOOLEAN): Whether symbol is actively traded
- `listing_date` (DATE): Date stock was first listed on exchange
- `delisting_date` (DATE): Date stock was delisted (NULL if still active)
- `ipo_date` (DATE): Initial Public Offering date
- `trading_status` (VARCHAR(20)): Current trading status (active, suspended, delisted)
- `exchange_status` (VARCHAR(20)): Exchange status (listed, delisted, transferred)
- `first_trading_date` (DATE): First date of actual trading data available
- `last_trading_date` (DATE): Last date of trading data (NULL if still trading)
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record last update timestamp

**Usage**: Referenced for symbol validation, metadata display, and temporal eligibility checking

#### 2. stock_prices_daily (TimescaleDB Hypertable)
**Purpose**: Primary time-series table for historical daily OHLCV data

```sql
CREATE TABLE IF NOT EXISTS stock_prices_daily (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open DECIMAL(10, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    close DECIMAL(10, 4),
    volume BIGINT,
    UNIQUE(time, symbol)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('stock_prices_daily', 'time', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);
```

**Columns**:
- `time` (TIMESTAMPTZ, NOT NULL): Trading date with timezone
- `symbol` (VARCHAR(10), NOT NULL): Stock ticker symbol
- `open` (DECIMAL(10,4)): Opening price
- `high` (DECIMAL(10,4)): Daily high price
- `low` (DECIMAL(10,4)): Daily low price
- `close` (DECIMAL(10,4)): Closing price
- `volume` (BIGINT): Trading volume

**TimescaleDB Configuration**:
- **Hypertable**: Partitioned by time dimension
- **Chunk Interval**: 1 month per chunk for optimal performance
- **Unique Constraint**: (time, symbol) prevents duplicate records

**Usage**: Primary data source for backtesting and analysis

#### 3. stock_trading_periods (Detailed Trading Period Tracking)
**Purpose**: Stores detailed trading period tracking for temporal validation

```sql
CREATE TABLE IF NOT EXISTS stock_trading_periods (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
    start_date DATE NOT NULL,             -- Start of trading period
    end_date DATE,                        -- End of trading period (NULL if ongoing)
    status VARCHAR(20) NOT NULL,          -- Trading status: active, suspended, delisted, halted
    reason VARCHAR(100),                  -- Reason for status change
    exchange VARCHAR(50),                 -- Exchange during this period
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Simple unique constraint to prevent basic overlaps
    UNIQUE(symbol, start_date)
);
```

**Columns**:
- `id` (SERIAL, PRIMARY KEY): Auto-incrementing period identifier
- `symbol` (VARCHAR(10), FOREIGN KEY): References stocks(symbol)
- `start_date` (DATE, NOT NULL): Start of trading period
- `end_date` (DATE): End of trading period (NULL if ongoing)
- `status` (VARCHAR(20), NOT NULL): Trading status (active, suspended, delisted, halted)
- `reason` (VARCHAR(100)): Reason for status change
- `exchange` (VARCHAR(50)): Exchange during this period
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record last update timestamp

**Relationships**:
- **Foreign Key**: `symbol` → `stocks(symbol)` with CASCADE DELETE

**Usage**: Detailed temporal tracking for complex trading period analysis and survivorship bias mitigation

#### 4. trading_sessions (Backtesting Sessions)
**Purpose**: Stores backtesting session configurations and metadata

```sql
CREATE TABLE IF NOT EXISTS trading_sessions (
    id SERIAL PRIMARY KEY,
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(12, 2),
    strategy_name VARCHAR(100),
    strategy_params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns**:
- `id` (SERIAL, PRIMARY KEY): Auto-incrementing session identifier
- `start_date` (DATE): Simulation start date
- `end_date` (DATE): Simulation end date
- `initial_capital` (DECIMAL(12,2)): Starting capital amount
- `strategy_name` (VARCHAR(100)): Trading strategy identifier
- `strategy_params` (JSONB): Strategy-specific parameters as JSON
- `created_at` (TIMESTAMP): Session creation timestamp

**Usage**: Tracks simulation configurations for result correlation

#### 5. trades_log (Trade Execution Records)
**Purpose**: Stores individual trade execution records from backtesting

```sql
CREATE TABLE IF NOT EXISTS trades_log (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES trading_sessions(id),
    symbol VARCHAR(10),
    trade_time TIMESTAMPTZ,
    action VARCHAR(10), -- 'BUY' or 'SELL'
    quantity INTEGER,
    price DECIMAL(10, 4),
    commission DECIMAL(8, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns**:
- `id` (SERIAL, PRIMARY KEY): Unique trade identifier
- `session_id` (INTEGER, FOREIGN KEY): References trading_sessions(id)
- `symbol` (VARCHAR(10)): Stock ticker symbol
- `trade_time` (TIMESTAMPTZ): Trade execution timestamp
- `action` (VARCHAR(10)): Trade direction ('BUY' or 'SELL')
- `quantity` (INTEGER): Number of shares traded
- `price` (DECIMAL(10,4)): Execution price per share
- `commission` (DECIMAL(8,2)): Trading commission/fees
- `created_at` (TIMESTAMP): Record creation timestamp

**Relationships**:
- **Foreign Key**: `session_id` → `trading_sessions(id)`

**Usage**: Detailed trade analysis and performance calculation

## Database Indexes

### Performance Indexes

#### 1. Stock Prices Daily Index
```sql
CREATE INDEX IF NOT EXISTS idx_daily_symbol_time 
ON stock_prices_daily (symbol, time DESC);
```
**Purpose**: Optimises symbol-specific time-range queries
**Usage**: Primary index for backtesting data retrieval

#### 2. Trades Session Index
```sql
CREATE INDEX IF NOT EXISTS idx_trades_session_id 
ON trades_log (session_id);
```
**Purpose**: Fast retrieval of trades by session
**Usage**: Session-based trade analysis

#### 3. Trades Symbol-Time Index
```sql
CREATE INDEX IF NOT EXISTS idx_trades_symbol_time 
ON trades_log (symbol, trade_time);
```
**Purpose**: Time-series analysis of trades per symbol
**Usage**: Trade pattern analysis

### Temporal Validation Indexes

#### 4. Stocks Listing Date Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_listing_date 
ON stocks (listing_date) WHERE listing_date IS NOT NULL;
```
**Purpose**: Fast queries for stocks by listing date
**Usage**: IPO date validation and temporal eligibility checking

#### 5. Stocks Delisting Date Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_delisting_date 
ON stocks (delisting_date) WHERE delisting_date IS NOT NULL;
```
**Purpose**: Fast queries for stocks by delisting date
**Usage**: Delisting date validation and temporal eligibility checking

#### 6. Stocks IPO Date Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_ipo_date 
ON stocks (ipo_date) WHERE ipo_date IS NOT NULL;
```
**Purpose**: Fast queries for stocks by IPO date
**Usage**: IPO date validation for survivorship bias mitigation

#### 7. Stocks Trading Status Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_trading_status 
ON stocks (trading_status);
```
**Purpose**: Fast filtering by trading status
**Usage**: Active/inactive stock filtering

#### 8. Stocks Temporal Range Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_temporal_range 
ON stocks (symbol, listing_date, delisting_date);
```
**Purpose**: Optimised temporal range queries for multiple stocks
**Usage**: Batch temporal validation operations

#### 9. Stocks First/Last Trading Date Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_first_last_trading 
ON stocks (symbol, first_trading_date, last_trading_date);
```
**Purpose**: Fast data availability checking
**Usage**: Validate actual trading data availability

#### 10. Trading Periods Symbol-Dates Index
```sql
CREATE INDEX IF NOT EXISTS idx_trading_periods_symbol_dates 
ON stock_trading_periods (symbol, start_date, end_date);
```
**Purpose**: Fast period-based queries
**Usage**: Detailed trading period analysis

#### 11. Trading Periods Status Index
```sql
CREATE INDEX IF NOT EXISTS idx_trading_periods_status 
ON stock_trading_periods (status);
```
**Purpose**: Filter trading periods by status
**Usage**: Status-based period analysis

#### 12. Trading Periods Date Range Index
```sql
CREATE INDEX IF NOT EXISTS idx_trading_periods_date_range 
ON stock_trading_periods USING gist (daterange(start_date, COALESCE(end_date, 'infinity'::date), '[]'));
```
**Purpose**: Advanced date range overlap queries
**Usage**: Complex temporal period analysis

#### 13. Stocks Temporal Validation Composite Index
```sql
CREATE INDEX IF NOT EXISTS idx_stocks_temporal_validation 
ON stocks (symbol, trading_status, listing_date, delisting_date) 
WHERE trading_status IN ('active', 'delisted');
```
**Purpose**: Optimised composite queries for temporal validation
**Usage**: High-performance survivorship bias checking

## Connection Management

### Python API (AsyncPG)

#### Connection Pool Configuration
```python
self.pool = await asyncpg.create_pool(
    self.database_url,
    min_size=10,        # Minimum connections
    max_size=50,        # Maximum connections
    command_timeout=60, # Query timeout (seconds)
    server_settings={
        'application_name': 'trading_platform_api',
    }
)
```

#### Cache Configuration
```python
# TTL Caches for performance optimisation
_stock_data_cache = TTLCache(maxsize=1024, ttl=300)     # 5 minutes
_stocks_list_cache = TTLCache(maxsize=1, ttl=300)       # 5 minutes
_validation_cache = TTLCache(maxsize=256, ttl=600)      # 10 minutes
```

### C++ Engine (libpq)

#### Connection String Format
```cpp
"host={host} port={port} dbname={database} user={username} password={password}"
```

#### Connection Management
- **RAII Pattern**: Automatic cleanup with destructors
- **Move Semantics**: Efficient connection transfer
- **Error Handling**: Result<T> pattern for safe operations

## Query Patterns

### Common Query Operations

#### 1. Symbol Validation
```sql
-- Python API
SELECT COUNT(*) as count FROM stock_prices_daily WHERE symbol = $1

-- C++ Engine
SELECT COUNT(*) as count FROM stock_prices_daily WHERE symbol = $1;
```

#### 2. Historical Price Retrieval
```sql
-- Python API (with pagination)
SELECT time, symbol, open, high, low, close, volume
FROM stock_prices_daily
WHERE symbol = $1 AND time >= $2 AND time <= $3
ORDER BY time ASC
LIMIT $4 OFFSET $5

-- C++ Engine (formatted timestamps)
SELECT to_char(time, 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"') as time, 
       symbol, open, high, low, close, volume
FROM stock_prices_daily 
WHERE symbol = $1 AND time >= $2 AND time <= $3 
ORDER BY time ASC;
```

#### 3. Available Symbols
```sql
SELECT DISTINCT symbol FROM stock_prices_daily ORDER BY symbol;
```

#### 4. Latest Price
```sql
SELECT close FROM stock_prices_daily 
WHERE symbol = $1 
ORDER BY time DESC LIMIT 1;
```

#### 5. Session Trades
```sql
SELECT symbol, action, quantity, price, commission, trade_time
FROM trades_log 
WHERE session_id = $1
ORDER BY trade_time ASC
LIMIT $2 OFFSET $3
```

### Batch Operations

#### Multi-Symbol Data Retrieval
```sql
-- Batch symbol validation
SELECT DISTINCT symbol
FROM stock_prices_daily 
WHERE symbol IN ($1, $2, ..., $N)

-- Batch price retrieval
SELECT symbol, time, open, high, low, close, volume 
FROM stock_prices_daily
WHERE symbol IN ($1, $2, ..., $N)
AND time BETWEEN $N+1 AND $N+2
ORDER BY symbol, time
```

## Data Loading and Migration

### CSV Data Loading Process

#### 1. Historical Data Import
```python
# CSVtoPostgres.py - Bulk data loading
execute_values(
    cur,
    """
    INSERT INTO stock_prices_daily 
    (time, symbol, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (time, symbol) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume;
    """,
    records
)
```

#### 2. Stock Metadata Import
```python
# Stock information with conflict resolution
INSERT INTO stocks (symbol, name, sector, exchange)
VALUES (%s, %s, %s, %s)
ON CONFLICT (symbol) DO UPDATE SET
    name = EXCLUDED.name,
    sector = EXCLUDED.sector,
    exchange = EXCLUDED.exchange;
```

### Data Initialisation
- **init.sql**: Executed automatically on container startup
- **Docker Volume Mount**: `/Database:/docker-entrypoint-initdb.d`
- **TimescaleDB Extension**: Created automatically during initialisation

## Performance Optimisations

### TimescaleDB Features

#### 1. Hypertable Partitioning
- **Time-based Chunks**: Monthly partitions for optimal query performance
- **Automatic Chunk Management**: Old chunks can be compressed or archived
- **Parallel Query Execution**: Queries span multiple chunks efficiently

#### 2. Compression (Future Enhancement)
```sql
-- Enable compression on old chunks
ALTER TABLE stock_prices_daily SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);
```

### Caching Strategy

#### API-Level Caching
- **Stock Data Cache**: 5-minute TTL, 1024 entries max
- **Symbol List Cache**: 5-minute TTL, single entry
- **Validation Cache**: 10-minute TTL, 256 entries max

#### Query Optimisations
- **Prepared Statements**: Used in C++ engine for SQL injection prevention
- **Connection Pooling**: Reduces connection overhead
- **Batch Queries**: Multi-symbol operations combined when possible

## Database Health Monitoring

### Health Check Queries

#### 1. Connection Test
```sql
SELECT NOW() as current_time
```

#### 2. Data Statistics
```sql
SELECT 
    (SELECT COUNT(DISTINCT symbol) FROM stock_prices_daily) as symbols_daily,
    (SELECT COUNT(*) FROM stock_prices_daily) as daily_records,
    (SELECT COUNT(*) FROM trading_sessions) as total_sessions,
    (SELECT COUNT(*) FROM trades_log) as total_trades
```

#### 3. Date Range Validation
```sql
SELECT 
    MIN(time) as earliest_date,
    MAX(time) as latest_date,
    COUNT(*) as record_count
FROM stock_prices_daily 
WHERE symbol = $1 AND time >= $2 AND time <= $3
```

### Docker Health Checks
```bash
# PostgreSQL container health
pg_isready -U trading_user -d simulated_trading_platform

# Application-level health
curl -f http://localhost:8000/health
```

## Error Handling and Logging

### Error Categories

#### 1. Connection Errors
- `DATABASE_CONNECTION_FAILED`: Connection establishment issues
- `DATABASE_NOT_CONNECTED`: Operations attempted without connection

#### 2. Query Errors
- `DATABASE_QUERY_FAILED`: SQL execution errors
- `DATA_PARSING_FAILED`: Result parsing issues

#### 3. Data Errors
- `DATA_SYMBOL_NOT_FOUND`: Invalid or missing symbols
- `VALIDATION_FAILED`: Input validation failures

### Logging Patterns

#### Python API
```python
logger.info("Database connection pool created successfully")
logger.error(f"Failed to create database pool: {e}")
logger.debug(f"Cache hit for stock data: {symbol}")
```

#### C++ Engine
```cpp
Logger::debug("DatabaseService::getHistoricalPrices called for symbol=", symbol);
Logger::error("Error in DatabaseService::getHistoricalPrices: ", result.getErrorMessage());
```

## Security Considerations

### Connection Security
- **Environment Variables**: Credentials stored in .env files
- **Prepared Statements**: SQL injection prevention
- **Connection Pooling**: Limited connection exposure

### Access Control
- **Single Database User**: `trading_user` with restricted permissions
- **Network Isolation**: Docker network container isolation
- **Port Mapping**: External access only through mapped ports

## Database Helper Functions

### Temporal Validation Functions

#### 1. is_stock_tradeable() Function
```sql
CREATE OR REPLACE FUNCTION is_stock_tradeable(
    stock_symbol VARCHAR(10),
    check_date DATE
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM stocks 
        WHERE symbol = stock_symbol
        AND trading_status = 'active'
        AND (listing_date IS NULL OR listing_date <= check_date)
        AND (delisting_date IS NULL OR delisting_date >= check_date)
    );
END;
$$ LANGUAGE plpgsql;
```
**Purpose**: Check if a stock was tradeable on a specific date
**Usage**: Real-time temporal validation during backtesting
**Parameters**: 
- `stock_symbol`: Stock ticker symbol
- `check_date`: Date to validate
**Returns**: Boolean indicating if stock was tradeable

#### 2. get_eligible_stocks_for_period() Function
```sql
CREATE OR REPLACE FUNCTION get_eligible_stocks_for_period(
    start_date_param DATE,
    end_date_param DATE
) RETURNS TABLE(symbol VARCHAR(10), listing_date DATE, delisting_date DATE) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.symbol,
        s.listing_date,
        s.delisting_date
    FROM stocks s
    WHERE s.trading_status = 'active'
    AND (s.listing_date IS NULL OR s.listing_date <= end_date_param)
    AND (s.delisting_date IS NULL OR s.delisting_date >= start_date_param);
END;
$$ LANGUAGE plpgsql;
```
**Purpose**: Get all stocks eligible for trading during a specific period
**Usage**: Batch temporal validation for large simulations
**Parameters**:
- `start_date_param`: Period start date
- `end_date_param`: Period end date
**Returns**: Table with eligible symbols and their temporal info

#### 3. update_stock_trading_dates() Function
```sql
CREATE OR REPLACE FUNCTION update_stock_trading_dates()
RETURNS VOID AS $$
BEGIN
    UPDATE stocks 
    SET 
        first_trading_date = subquery.min_date,
        last_trading_date = subquery.max_date
    FROM (
        SELECT 
            symbol,
            MIN(time::date) as min_date,
            MAX(time::date) as max_date
        FROM stock_prices_daily
        GROUP BY symbol
    ) as subquery
    WHERE stocks.symbol = subquery.symbol;
    
    RAISE NOTICE 'Updated trading dates for % stocks', (SELECT COUNT(*) FROM stocks WHERE first_trading_date IS NOT NULL);
END;
$$ LANGUAGE plpgsql;
```
**Purpose**: Automatically populate first/last trading dates from actual data
**Usage**: Data maintenance and validation
**Returns**: Void (logs count of updated stocks)

### Database Triggers

#### 1. Update Timestamp Trigger Function
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```
**Purpose**: Automatically update updated_at timestamps
**Usage**: Maintain audit trail for data changes

#### 2. Stocks Table Trigger
```sql
CREATE TRIGGER update_stocks_updated_at 
    BEFORE UPDATE ON stocks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

#### 3. Trading Periods Table Trigger
```sql
CREATE TRIGGER update_trading_periods_updated_at 
    BEFORE UPDATE ON stock_trading_periods 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

## Backup and Recovery

### Data Persistence
- **Docker Volume**: `postgres_data` for persistent storage
- **TimescaleDB**: Built-in replication and backup capabilities

### Recovery Procedures
1. **Container Recovery**: Docker restart with health checks
2. **Data Recovery**: Volume restoration from backups
3. **Schema Recovery**: `init.sql` re-execution

## Database Integration Points

### API Endpoints Using Database
- **GET /stocks**: Symbol listing with pagination
- **GET /stocks/{symbol}/data**: Historical price data
- **GET /stocks/{symbol}/date-range**: Available data ranges
- **POST /simulation/validate**: Symbol and date validation
- **GET /simulation/{id}/results**: Trade and session data

#### Temporal Validation Endpoints
- **POST /stocks/validate-temporal**: Batch temporal validation for multiple stocks
- **GET /stocks/{symbol}/temporal-info**: Temporal information for a stock
- **POST /stocks/check-tradeable**: Check if a stock was tradeable on a specific date
- **GET /stocks/eligible-for-period**: Get stocks eligible for trading during a period

### C++ Engine Integration
- **Data Retrieval**: Historical price queries for backtesting
- **Symbol Validation**: Pre-execution symbol verification
- **Result Storage**: Trade logging and session tracking

#### Dynamic Temporal Validation
- **Real-time Validation**: `checkStockTradeable()` calls during daily trading loop
- **Batch Validation**: `validateSymbolsForPeriod()` for initial validation
- **Temporal Info**: `getStockTemporalInfo()` for detailed stock information
- **Dynamic Trading**: Stocks only traded when actually available (IPO to delisting)

### Frontend Integration
- **Real-time Queries**: Stock data for chart display
- **Pagination Support**: Large dataset handling
- **Error Handling**: User-friendly error messages
