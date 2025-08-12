-- Initialize TimescaleDB and create database schema
-- This file will be automatically executed by PostgreSQL on container startup

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create stocks metadata table with temporal tracking
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

-- Create stock trading periods table for detailed trading period tracking
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
    action VARCHAR(10),
    quantity INTEGER,
    price DECIMAL(10, 4),
    commission DECIMAL(8, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_daily_symbol_time 
ON stock_prices_daily (symbol, time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_session_id 
ON trades_log (session_id);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time 
ON trades_log (symbol, trade_time);

-- Create temporal validation indexes
CREATE INDEX IF NOT EXISTS idx_stocks_listing_date 
ON stocks (listing_date) WHERE listing_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stocks_delisting_date 
ON stocks (delisting_date) WHERE delisting_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stocks_ipo_date 
ON stocks (ipo_date) WHERE ipo_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stocks_trading_status 
ON stocks (trading_status);

CREATE INDEX IF NOT EXISTS idx_stocks_temporal_range 
ON stocks (symbol, listing_date, delisting_date);

CREATE INDEX IF NOT EXISTS idx_stocks_first_last_trading 
ON stocks (symbol, first_trading_date, last_trading_date);

-- Indexes for stock_trading_periods table
CREATE INDEX IF NOT EXISTS idx_trading_periods_symbol_dates 
ON stock_trading_periods (symbol, start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_trading_periods_status 
ON stock_trading_periods (status);

CREATE INDEX IF NOT EXISTS idx_trading_periods_date_range 
ON stock_trading_periods USING gist (daterange(start_date, COALESCE(end_date, 'infinity'::date), '[]'));

-- Composite index for temporal validation queries
CREATE INDEX IF NOT EXISTS idx_stocks_temporal_validation 
ON stocks (symbol, trading_status, listing_date, delisting_date) 
WHERE trading_status IN ('active', 'delisted');

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_stocks_updated_at 
    BEFORE UPDATE ON stocks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_periods_updated_at 
    BEFORE UPDATE ON stock_trading_periods 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Helper function for temporal stock validation
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

-- Helper function to get eligible stocks for a given date range
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

-- Create function to populate first_trading_date and last_trading_date automatically
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

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
END
$$;