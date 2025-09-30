# Database Technical Documentation

## 1. Introduction

This document provides a technical reference for the TimescaleDB database used by the Simulated Trading Platform.
### 1.1. Technology Stack

-   **Database Engine**: TimescaleDB (running on PostgreSQL 15).
-   **Deployment**: Docker container with a persistent volume for data.
-   **Python Connector**: `asyncpg` for asynchronous access with connection pooling.
-   **C++ Connector**: `libpq-fe` (standard PostgreSQL C library).

### 1.2. Core Concepts

-   **Time-Series Data**: The schema is optimized for time-series data (stock prices) using TimescaleDB hypertables.
-   **Temporal Accuracy**: A key feature is the mitigation of survivorship bias. The schema tracks stock listing/delisting dates and trading periods to ensure backtests are run only against historically accurate data.

## 2. Database Schema

### 2.1. `stocks`

Stores metadata for each stock, including critical information for temporal validation.

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

### 2.2. `stock_prices_daily`

The primary hypertable for storing daily OHLCV (Open, High, Low, Close, Volume) time-series data.

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
- **Note**: This is a TimescaleDB hypertable partitioned by the `time` column into one-month chunks for efficient time-based queries.

### 2.3. `stock_trading_periods`

Provides granular tracking of a stock's trading status over time, supporting complex temporal validation scenarios.

```sql
CREATE TABLE IF NOT EXISTS stock_trading_periods (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL, -- e.g., active, suspended, halted
    reason VARCHAR(100),
    exchange VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, start_date)
);
```

### 2.4. `trading_sessions`

Stores the configuration for each backtesting session.

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

### 2.5. `trades_log`

Logs every individual trade executed during a backtesting session.

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

## 3. Indexing Strategy

Indexes are critical for query performance, especially for time-series and temporal validation queries.

### Primary Performance Indexes
-   **Primary Backtesting Index**: `CREATE INDEX IF NOT EXISTS idx_daily_symbol_time ON stock_prices_daily (symbol, time DESC);`
-   **Trade Symbol Time Index**: `CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades_log (symbol, trade_time);`
-   **Parallel Query Optimization**: Index supports concurrent access from multiple parallel groups.
-   **Trade Retrieval**: `CREATE INDEX IF NOT EXISTS idx_trades_session_id ON trades_log (session_id);`

### Temporal Validation Indexes
-   **Date-based Lookups**: Separate indexes on `listing_date`, `delisting_date`, and `ipo_date`.
    -   `CREATE INDEX IF NOT EXISTS idx_stocks_listing_date ON stocks (listing_date) WHERE listing_date IS NOT NULL;`
    -   `CREATE INDEX IF NOT EXISTS idx_stocks_delisting_date ON stocks (delisting_date) WHERE delisting_date IS NOT NULL;`
    -   `CREATE INDEX IF NOT EXISTS idx_stocks_ipo_date ON stocks (ipo_date) WHERE ipo_date IS NOT NULL;`
-   **Status Filtering**: `CREATE INDEX IF NOT EXISTS idx_stocks_trading_status ON stocks (trading_status);`
-   **Composite Validation**: `CREATE INDEX IF NOT EXISTS idx_stocks_temporal_validation ON stocks (symbol, trading_status, listing_date, delisting_date) WHERE trading_status = 'active';`
-   **Period Overlap**: `CREATE INDEX IF NOT EXISTS idx_trading_periods_date_range ON stock_trading_periods USING gist (daterange(start_date, COALESCE(end_date, 'infinity'::date), '[]'));`

### Additional Performance Indexes
-   **Volume Analysis**: `CREATE INDEX IF NOT EXISTS idx_daily_volume ON stock_prices_daily (volume DESC, time);`
-   **Price Range Queries**: `CREATE INDEX IF NOT EXISTS idx_daily_price_range ON stock_prices_daily (symbol, high, low, time);`
-   **Session Performance**: `CREATE INDEX IF NOT EXISTS idx_sessions_date_range ON trading_sessions (start_date, end_date);`
-   **Multi-symbol Queries**: `CREATE INDEX IF NOT EXISTS idx_daily_multi_symbol ON stock_prices_daily (time, symbol) WHERE symbol = ANY(ARRAY['AAPL','GOOGL','MSFT']);`

## 4. Stored Procedures and Triggers

Custom database logic is used for validation and maintenance.

### 4.1. Helper Functions (PL/pgSQL)

-   **`is_stock_tradeable(symbol, date)`**: Checks if a stock was listed and not delisted on a specific date. Used for real-time validation during backtesting.
-   **`get_eligible_stocks_for_period(start_date, end_date)`**: Returns all stocks that were tradeable throughout a given period. Used for setting up a simulation's universe of stocks.
-   **`update_stock_trading_dates()`**: Populates the `first_trading_date` and `last_trading_date` columns in the `stocks` table based on the actual data available in `stock_prices_daily`.

### 4.2. Triggers

-   **`update_updated_at_column()`**: A trigger function that automatically sets the `updated_at` field to the current timestamp on any row update. This is applied to the `stocks` and `stock_trading_periods` tables.

## 5. Application Integration

### 5.1. Connection Management

-   **Python (asyncpg)**: A `DatabaseConnectionManager` class manages an `asyncpg` connection pool. Shared across parallel execution groups for consistency.
-   **C++ (libpq)**: Uses a standard connection string: `"host={host} port={port} dbname={database} user={username} password={password}"`. Each parallel group maintains its own connection.

### 5.2. Data Access Layer (Python)

The API uses a repository and service pattern to interact with the database.

-   **`QueryExecutor`**: A low-level component that executes raw SQL queries against the connection pool and returns results.
-   **`CacheManager`**: Provides an in-memory, time-to-live (TTL) cache for frequently requested data, such as stock lists and validation results, reducing database load.
-   **`StockDataRepository`**: Exposes high-level methods for accessing stock data (e.g., `get_stock_prices`, `validate_symbol_exists`). It uses `QueryExecutor` and `CacheManager`.
-   **`TemporalValidationService`**: Encapsulates the business logic for survivorship bias checks, using the database helper functions and temporal tables.

### 5.3. Common Query Patterns

**Time-Series Data Queries:**
-   **Historical Price Retrieval**: `SELECT open, high, low, close, volume FROM stock_prices_daily WHERE symbol = $1 AND time >= $2 AND time <= $3 ORDER BY time ASC`
-   **Date Range Availability**: `SELECT MIN(time::date), MAX(time::date) FROM stock_prices_daily WHERE symbol = $1`
-   **Latest Price Data**: `SELECT * FROM stock_prices_daily WHERE symbol = $1 ORDER BY time DESC LIMIT 1`

**Temporal Validation Queries:**
-   **Symbol Existence**: `SELECT 1 FROM stocks WHERE symbol = $1`
-   **Trading Status Check**: `SELECT is_stock_tradeable($1, $2)` - Uses stored function for temporal validation
-   **Eligible Stocks for Period**: `SELECT * FROM get_eligible_stocks_for_period($1, $2)` - Returns table of valid stocks
-   **Active Stock Filtering**: `SELECT symbol FROM stocks WHERE trading_status = 'active' AND listing_date <= $1`

**Simulation and Trading Queries:**
-   **Session Trade Retrieval**: `SELECT symbol, trade_time, action, quantity, price FROM trades_log WHERE session_id = $1 ORDER BY trade_time ASC`
-   **Performance Analysis**: `SELECT * FROM trading_sessions WHERE id = $1`
-   **Bulk Symbol Validation**: `SELECT symbol FROM stocks WHERE symbol = ANY($1) AND trading_status = 'active'`

## 6. Operations and Configuration

### 6.1. Connection Parameters

Connection details are managed via environment variables.

-   `DB_HOST`: `postgres` (within Docker), `localhost` (for local testing)
-   `DB_PORT`: `5432` (within Docker), `5433` (for local testing)
-   `DB_NAME`: `simulated_trading_platform`
-   `DB_USER`: `trading_user`
-   `DB_PASSWORD`: `trading_password`
-   `DATABASE_URL`: A full connection string for the Python API, e.g., `postgresql://trading_user:trading_password@postgres:5432/simulated_trading_platform`

### 6.2. Data Loading and Migration

-   **Initial Schema**: The `init.sql` script in the `/Database` directory creates all tables, indexes, and functions when the Docker container is first started.
-   **Bulk Data Loading**: The `Database/DataGathering.py` script is used for bulk-importing historical data from CSV files into the `stock_prices_daily` table, using an `ON CONFLICT` clause to handle updates.

### 6.3. Health and Monitoring

-   **Docker Health Check**: The PostgreSQL container uses `pg_isready` to confirm the database is accepting connections.
-   **Application Health Check**: The API's `/health` endpoint runs a `SELECT NOW()` query to verify database connectivity.

### 6.4. Security

-   **Credentials**: Managed via `.env` files and environment variables, not hard-coded.
-   **Network Isolation**: The database container is isolated on a dedicated Docker network.
-   **Access Control**: A single, non-privileged `trading_user` is used by the applications.
-   **SQL Injection**: All queries are executed with parameterized inputs (e.g., via `asyncpg` in Python or prepared statements in C++).