#!/usr/bin/env python3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import json
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVToPostgreSQLLoader:
    def __init__(self, db_config: Dict[str, str], data_dir: str = "historical_data"):
        
        # Initialize loader
        # Args:
        #    db_config: PostgreSQL connection parameters
        #    data_dir: Directory containing CSV files
        
        self.db_config = db_config
        self.data_dir = data_dir
        
    def create_timescale_tables(self):
        # Create TimescaleDB tables with temporal tracking
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Create extension if not exists
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Create stocks metadata table with temporal tracking
            cur.execute("""
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
            """)
            
            # Create historical price data table
            cur.execute("""
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
            """)
            
            # Convert to hypertable
            cur.execute("""
                SELECT create_hypertable('stock_prices_daily', 'time', 
                    chunk_time_interval => INTERVAL '1 month',
                    if_not_exists => TRUE
                );
            """)
            
            # Create stock trading periods table for detailed trading period tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_trading_periods (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
                    start_date DATE NOT NULL,             -- Start of trading period
                    end_date DATE,                        -- End of trading period (NULL if ongoing)
                    status VARCHAR(20) NOT NULL,          -- Trading status: active, suspended, delisted, halted
                    reason VARCHAR(100),                  -- Reason for status change
                    exchange VARCHAR(50),                 -- Exchange during this period
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create tables for backtesting results
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id SERIAL PRIMARY KEY,
                    start_date DATE,
                    end_date DATE,
                    initial_capital DECIMAL(12, 2),
                    strategy_name VARCHAR(100),
                    strategy_params JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
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
            """)
            
            # Create temporal validation indexes
            cur.execute("""
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
                
                CREATE INDEX IF NOT EXISTS idx_trading_periods_symbol_dates 
                ON stock_trading_periods (symbol, start_date, end_date);
                
                CREATE INDEX IF NOT EXISTS idx_trading_periods_status 
                ON stock_trading_periods (status);
                
                CREATE INDEX IF NOT EXISTS idx_stocks_temporal_validation 
                ON stocks (symbol, trading_status, listing_date, delisting_date) 
                WHERE trading_status IN ('active', 'delisted');
            """)
            
            # Helper functions for temporal stock validation
            cur.execute("""
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
            """)
            
            conn.commit()
            logger.info("TimescaleDB tables and temporal validation functions created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    
    def load_stock_info(self):
        # Load stock metadata from JSON file
        info_file = os.path.join(self.data_dir, "stock_info.json")
        
        if not os.path.exists(info_file):
            logger.warning("No stock_info.json found")
            return
            
        with open(info_file, 'r') as f:
            stock_info = json.load(f)
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            for symbol, info in stock_info.items():
                # Safely parse date fields
                ipo_date = info.get('ipo_date') if info.get('ipo_date') else None
                listing_date = info.get('listing_date') if info.get('listing_date') else None
                delisting_date = info.get('delisting_date') if info.get('delisting_date') else None
                first_trading_date = info.get('first_trading_date') if info.get('first_trading_date') else None
                last_trading_date = info.get('last_trading_date') if info.get('last_trading_date') else None
                
                cur.execute("""
                    INSERT INTO stocks (
                        symbol, name, sector, exchange, 
                        ipo_date, listing_date, delisting_date,
                        trading_status, exchange_status,
                        first_trading_date, last_trading_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        name = EXCLUDED.name,
                        sector = EXCLUDED.sector,
                        exchange = EXCLUDED.exchange,
                        ipo_date = EXCLUDED.ipo_date,
                        listing_date = EXCLUDED.listing_date,
                        delisting_date = EXCLUDED.delisting_date,
                        trading_status = EXCLUDED.trading_status,
                        exchange_status = EXCLUDED.exchange_status,
                        first_trading_date = EXCLUDED.first_trading_date,
                        last_trading_date = EXCLUDED.last_trading_date,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    symbol, 
                    info.get('name', symbol), 
                    info.get('sector', ''), 
                    info.get('exchange', ''),
                    ipo_date,
                    listing_date, 
                    delisting_date,
                    info.get('trading_status', 'active'),
                    info.get('exchange_status', 'listed'),
                    first_trading_date,
                    last_trading_date
                ))
            
            conn.commit()
            logger.info(f"Loaded metadata for {len(stock_info)} stocks")
            
        except Exception as e:
            logger.error(f"Error loading stock info: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def load_daily_data(self):
        # Load daily price data from CSV
        daily_dir = os.path.join(self.data_dir, "daily")
        
        if not os.path.exists(daily_dir):
            logger.warning("No daily data directory found")
            return
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        for filename in os.listdir(daily_dir):
            if not filename.endswith('.csv'):
                continue
                
            symbol = filename.replace('_daily.csv', '')
            filepath = os.path.join(daily_dir, filename)
            
            try:
                # Read CSV
                df = pd.read_csv(filepath, parse_dates=['date'])
                
                # Prepare data for insertion
                records = []
                for _, row in df.iterrows():
                    records.append((
                        row['date'],
                        symbol,
                        row['open'],
                        row['high'],
                        row['low'],
                        row['close'],
                        row['volume']
                    ))
                
                # Bulk insert
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
                
                conn.commit()
                logger.info(f"Loaded {len(records)} daily records for {symbol}")
                
            except Exception as e:
                logger.error(f"Error loading daily data for {symbol}: {e}")
                conn.rollback()
        
        cur.close()
        conn.close()
    
    def verify_data(self):
        # Verify data was loaded correctly
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Check daily data
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT symbol) as symbols,
                    COUNT(*) as total_records,
                    MIN(time) as earliest,
                    MAX(time) as latest
                FROM stock_prices_daily;
            """)
            
            daily_stats = cur.fetchone()
            print("\nDaily Data Statistics")
            print(f"Symbols: {daily_stats[0]}")
            print(f"Total Records: {daily_stats[1]:,}")
            print(f"Date Range: {daily_stats[2]} to {daily_stats[3]}")  
        finally:
            cur.close()
            conn.close()
    
    def load_all_data(self):
        # Load all data from CSV to PostgreSQL
        logger.info("Starting data load process:")
        
        # Create tables
        self.create_timescale_tables()
        
        # Load stock metadata
        self.load_stock_info()
        
        # Load daily data
        self.load_daily_data()
        
        # Verify
        self.verify_data()
        
        logger.info("Data load complete!")

if __name__ == "__main__":
    # Database configuration from env // using TEST_* for local
    DB_CONFIG = {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "database": os.getenv("TEST_DB_NAME", "simulated_trading_platform"),
        "user": os.getenv("TEST_DB_USER", "trading_user"),
        "password": os.getenv("TEST_DB_PASSWORD", "trading_password"),
        "port": int(os.getenv("TEST_DB_PORT", "5433"))
    }
    
    # Initialize loader
    loader = CSVToPostgreSQLLoader(DB_CONFIG, "historical_data")
    
    # Load all data
    loader.load_all_data()
    
    print("\nData successfully loaded into PostgreSQL!")