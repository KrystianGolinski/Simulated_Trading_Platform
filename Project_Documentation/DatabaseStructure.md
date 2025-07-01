# Database Structure Documentation

## Overview

Using TimescaleDB (PostgreSQL extension) as its primary database technology, specifically designed for time-series data handling. The database is deployed via Docker containers with comprehensive health monitoring and connection pooling.

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

#### 1. stocks (Metadata Table)
**Purpose**: Stores metadata about available stock symbols

```sql
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(100),
    exchange VARCHAR(50),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns**:
- `symbol` (VARCHAR(10), PRIMARY KEY): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
- `name` (VARCHAR(255)): Full company name
- `sector` (VARCHAR(100)): Business sector classification
- `exchange` (VARCHAR(50)): Stock exchange (NYSE, NASDAQ, etc.)
- `active` (BOOLEAN): Whether symbol is actively traded
- `created_at` (TIMESTAMP): Record creation timestamp

**Usage**: Referenced for symbol validation and metadata display

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

#### 3. trading_sessions (Backtesting Sessions)
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

#### 4. trades_log (Trade Execution Records)
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

### C++ Engine Integration
- **Data Retrieval**: Historical price queries for backtesting
- **Symbol Validation**: Pre-execution symbol verification
- **Result Storage**: Trade logging and session tracking

### Frontend Integration
- **Real-time Queries**: Stock data for chart display
- **Pagination Support**: Large dataset handling
- **Error Handling**: User-friendly error messages
