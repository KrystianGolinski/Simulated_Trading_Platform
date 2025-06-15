-- Initialize TimescaleDB and create database schema
-- This file will be automatically executed by PostgreSQL on container startup

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create stocks metadata table
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(100),
    exchange VARCHAR(50),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create historical daily price data table
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

-- Convert to TimescaleDB hypertable for efficient time-series operations
SELECT create_hypertable('stock_prices_daily', 'time', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Create 1-minute intraday price data table
CREATE TABLE IF NOT EXISTS stock_prices_1min (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open DECIMAL(10, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    close DECIMAL(10, 4),
    volume BIGINT,
    vwap DECIMAL(10, 4),
    UNIQUE(time, symbol)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('stock_prices_1min', 'time', 
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- Create continuous aggregate for hourly data (performance optimization)
CREATE MATERIALIZED VIEW IF NOT EXISTS stock_prices_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS time,
    symbol,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume
FROM stock_prices_1min
GROUP BY time_bucket('1 hour', time), symbol
WITH NO DATA;

-- Add refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('stock_prices_hourly',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create trading sessions table for backtesting
CREATE TABLE IF NOT EXISTS trading_sessions (
    id SERIAL PRIMARY KEY,
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(12, 2),
    strategy_name VARCHAR(100),
    strategy_params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trades log table for individual trade records
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

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_daily_symbol_time 
ON stock_prices_daily (symbol, time DESC);

CREATE INDEX IF NOT EXISTS idx_1min_symbol_time 
ON stock_prices_1min (symbol, time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_session_id 
ON trades_log (session_id);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time 
ON trades_log (symbol, trade_time);

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
END
$$;