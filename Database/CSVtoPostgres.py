#!/usr/bin/env python3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import json
import logging
from datetime import datetime
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
        # Create TimescaleDB tables matching your architecture
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Create extension if not exists
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Create stocks metadata table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(255),
                    sector VARCHAR(100),
                    exchange VARCHAR(50),
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create historical price data table (matching your architecture)
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
            
            # Create tables for backtesting results (matching your architecture)
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
            
            conn.commit()
            logger.info("TimescaleDB tables created successfully")
            
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
                cur.execute("""
                    INSERT INTO stocks (symbol, name, sector, exchange)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        name = EXCLUDED.name,
                        sector = EXCLUDED.sector,
                        exchange = EXCLUDED.exchange;
                """, (symbol, info['name'], info['sector'], info['exchange']))
            
            conn.commit()
            logger.info(f"Loaded metadata for {len(stock_info)} stocks")
            
        except Exception as e:
            logger.error(f"Error loading stock info: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def load_daily_data(self):
        # Load daily price data from CSV files
        daily_dir = os.path.join(self.data_dir, "daily", "cleaned")
        
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
        # Load all data from CSV files to PostgreSQL
        logger.info("Starting data load process...")
        
        # Create tables
        self.create_timescale_tables()
        
        # Load stock metadata
        self.load_stock_info()
        
        # Load daily data
        self.load_daily_data()
        
        # Verify
        self.verify_data()
        
        logger.info("Data load complete!")


# Usage
if __name__ == "__main__":
    # Database configuration for Docker environment
    DB_CONFIG = {
        "host": "localhost",
        "database": "simulated_trading_platform",
        "user": "trading_user",
        "password": "trading_password",
        "port": 5433
    }
    
    # Initialize loader
    loader = CSVToPostgreSQLLoader(DB_CONFIG, "historical_data")
    
    # Load all data
    loader.load_all_data()
    
    print("\nData successfully loaded into PostgreSQL!")