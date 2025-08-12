#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreeDataCollector:
    
    # Data collector with data cleaning
    # Collects data from Yahoo Finance, cleans it, and saves directly to PostgreSQL database
    
    def __init__(self, db_config: Dict[str, str]):
        # Initialize data collector with database configuration
        self.db_config = db_config
        
        # Test database connection with retry for initialization
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(**self.db_config)
                conn.close()
                logger.info("Database connection test successful")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Database connection attempt {attempt + 1} failed, retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                    raise

    def save_stock_info_to_database(self, stock_info: Dict[str, Dict]):
        # Load stock metadata directly to PostgreSQL
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
            logger.info(f"Loaded metadata for {len(stock_info)} stocks to database")
            
        except Exception as e:
            logger.error(f"Error loading stock info to database: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def save_daily_data_to_database(self, df: pd.DataFrame, symbol: str):
        # Save cleaned DataFrame directly to PostgreSQL
        if df.empty:
            return
            
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
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
            logger.info(f"Loaded {len(records)} daily records for {symbol} to database")
            
        except Exception as e:
            logger.error(f"Error loading daily data for {symbol} to database: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def verify_database_data(self):
        # Verify data was loaded correctly to database
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
            print("\nDatabase Data Statistics")
            print(f"Symbols: {daily_stats[0]}")
            print(f"Total Records: {daily_stats[1]:,}")
            print(f"Date Range: {daily_stats[2]} to {daily_stats[3]}")
            
        except Exception as e:
            logger.error(f"Error verifying database data: {e}")
        finally:
            cur.close()
            conn.close()

    def fetch_stock_info_and_data(self, symbols: List[str]) -> Dict[str, Dict]:
        # Fetch stock metadata and historical data from Yahoo Finance
        # Returns: Dict containing both stock info and historical data for each symbol
        stock_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Get basic stock information
                basic_info = {
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'sector': info.get('sector', ''),
                    'exchange': info.get('exchange', ''),
                    'currency': info.get('currency', 'USD'),
                    'market_cap': info.get('marketCap', 0)
                }
                
                # Fetch all historical data
                hist_data = ticker.history(period="max", auto_adjust=False)
                
                # Extract temporal information from data
                temporal_info = self._extract_temporal_info_from_data(info, hist_data, symbol)
                
                # Combine all information
                stock_info = {**basic_info, **temporal_info}
                
                # Store both info and historical data
                stock_data[symbol] = {
                    'info': stock_info,
                    'historical_data': hist_data
                }
                
                logger.info(f"Fetched info and data for {symbol} (IPO: {temporal_info.get('ipo_date', 'Unknown')})")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching info and data for {symbol}: {e}")
                stock_data[symbol] = {
                    'info': {
                        'name': symbol,
                        'sector': 'Unknown',
                        'exchange': 'Unknown',
                        'ipo_date': None,
                        'listing_date': None,
                        'delisting_date': None,
                        'trading_status': 'unknown',
                        'exchange_status': 'unknown'
                    },
                    'historical_data': pd.DataFrame()
                }
        
        return stock_data
    
    def _extract_temporal_info_from_data(self, info: Dict, hist_data: pd.DataFrame, symbol: str) -> Dict:
        # Extract temporal information from pre-fetched historical data
        temporal_data = {}
        
        try:
            # Get IPO date
            ipo_date = None
            first_trading_date = None
            last_trading_date = None
            
            # Try different fields that might contain IPO information
            if 'firstTradeDateEpochUtc' in info and info['firstTradeDateEpochUtc']:
                ipo_date = datetime.fromtimestamp(info['firstTradeDateEpochUtc']).strftime('%Y-%m-%d')
            elif 'sharesOutstanding' in info and info.get('foundingDate'):
                # Some tickers have founding date
                founding_date = info.get('foundingDate')
                if founding_date:
                    ipo_date = founding_date
            
            # Use historical data to determine actual first/last trading dates
            if not hist_data.empty:
                first_trading_date = hist_data.index[0].strftime('%Y-%m-%d')
                last_trading_date = hist_data.index[-1].strftime('%Y-%m-%d')
                
                # If no IPO date found from API, use first trading date
                if not ipo_date:
                    ipo_date = first_trading_date
                    logger.debug(f"Using first trading date as IPO for {symbol}: {first_trading_date}")
            
            # Determine trading status
            trading_status = 'active'
            exchange_status = 'listed'
            delisting_date = None
            
            # Check if stock is still actively trading by examining last trading date
            if last_trading_date:
                last_date = datetime.strptime(last_trading_date, '%Y-%m-%d')
                # If last trading is more than 30 days ago then likely delisted
                if last_date < datetime.now() - timedelta(days=30):
                    trading_status = 'delisted'
                    exchange_status = 'delisted'
                    delisting_date = last_trading_date
                    logger.info(f"Detected potential delisting for {symbol}, last trade: {last_trading_date}")
            
            # Handle special cases for indices and ETFs
            if symbol.startswith('^') or symbol in ['SPY', 'QQQ', 'IWM']:
                trading_status = 'active'
                exchange_status = 'listed'
                # Indices don't have IPO dates in traditional sense
                if not ipo_date and symbol.startswith('^'):
                    ipo_date = None  # Will be determined from first available data
            
            temporal_data = {
                'ipo_date': ipo_date,
                'listing_date': ipo_date,
                'delisting_date': delisting_date,
                'trading_status': trading_status,
                'exchange_status': exchange_status,
                'first_trading_date': first_trading_date,
                'last_trading_date': last_trading_date
            }
            
            logger.debug(f"Temporal info for {symbol}: {temporal_data}")
            
        except Exception as e:
            logger.error(f"Error extracting temporal info for {symbol}: {e}")
            temporal_data = {
                'ipo_date': None,
                'listing_date': None,
                'delisting_date': None,
                'trading_status': 'unknown',
                'exchange_status': 'unknown',
                'first_trading_date': None,
                'last_trading_date': None
            }
        
        return temporal_data
    
    def process_historical_data(self, hist_data: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Process pre-fetched historical data for the specified date range
        # Args:
        #    hist_data: Pre-fetched historical data DataFrame
        #    symbol: Stock symbol
        #    start_date: Start date (YYYY-MM-DD)
        #    end_date: End date (YYYY-MM-DD)
        # Returns:
        #    DataFrame with processed OHLCV data for the specified date range
        
        try:
            if hist_data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return pd.DataFrame()
            
            # Create a copy to avoid modifying the original data
            df = hist_data.copy()
            
            # Filter data to the requested date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if df.empty:
                logger.warning(f"No data found for {symbol} in date range {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Fix for MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Reset index to have date as a column
            df.reset_index(inplace=True)
            df['symbol'] = symbol
            
            # Rename columns to match schema
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            logger.info(f"Processed {len(df)} daily records for {symbol} in date range {start_date} to {end_date}")
            return df
            
        except Exception as e:
            logger.error(f"Error processing historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Clean the data during collection
        if df.empty:
            return df
            
        df = df.copy()
        
        # Handle stock splits and dividends
        date_col = 'date'
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Calculate adjustment factor from close vs adj_close
        df['adj_factor'] = df['adj_close'] / df['close']
        
        # Apply adjustments to OHLCV data to match adj_close
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col] * df['adj_factor']
        
        # Adjust volume inversely for splits
        df['volume'] = df['volume'] / df['adj_factor']
        
        # Remove adjustment helper column
        df = df.drop(['adj_factor'], axis=1)
        
        # Remove duplicates by date
        df['date_only'] = df[date_col].dt.date
        df = df.drop_duplicates(subset=['date_only', 'symbol'], keep='first')
        df = df.drop('date_only', axis=1)
        
        # Normalize price data
        price_columns = ['open', 'high', 'low', 'close', 'adj_close']
        for col in price_columns:
            df[col] = df[col].round(4)
        
        # Remove rows with negative or zero prices
        for col in price_columns:
            df = df[df[col] > 0]
        
        # Remove rows with negative volume
        df = df[df['volume'] >= 0]
        
        # Validate OHLC relationships
        valid_ohlc = (
            (df['high'] >= df['open']) &
            (df['high'] >= df['close']) &
            (df['low'] <= df['open']) &
            (df['low'] <= df['close']) &
            (df['high'] >= df['low'])
        )
        
        invalid_count = (~valid_ohlc).sum()
        if invalid_count > 0:
            logger.warning(f"Removing {invalid_count} rows with invalid OHLC relationships")
            df = df[valid_ohlc]
        
        # Sort by date
        df = df.sort_values(date_col)
        
        return df
    
    def collect_all_data(self, symbols: List[str], start_date: str, end_date: str):
        # Collect all available data for given symbols and save directly to database
        # Args:
        # symbols: List of stock symbols
        # start_date: Start date for daily data (YYYY-MM-DD)
        # end_date: End date for daily data (YYYY-MM-DD)

        # Fetch stock info and historical data
        logger.info("Fetching stock information and historical data:")
        stock_data = self.fetch_stock_info_and_data(symbols)
        
        # Extract stock info for database insertion
        stock_info = {symbol: data['info'] for symbol, data in stock_data.items()}

        # Process and save historical data for each symbol
        logger.info("Processing historical data for date range and saving to database:")
        for symbol in symbols:
            logger.info(f"Processing {symbol}:")
            
            # Use historical data and filter to appropriate dates
            hist_data = stock_data[symbol]['historical_data']
            daily_df = self.process_historical_data(hist_data, symbol, start_date, end_date)
            
            if not daily_df.empty:
                # Clean the data before saving
                original_count = len(daily_df)
                daily_df = self.clean_data(daily_df)
                cleaned_count = len(daily_df)
                
                if cleaned_count < original_count:
                    logger.info(f"Cleaned {symbol}: {original_count} -> {cleaned_count} rows ({original_count - cleaned_count} removed)")
                
                # Update stock info with actual trading dates from processed data
                if symbol in stock_info and not daily_df.empty:
                    first_date = daily_df['date'].min()
                    last_date = daily_df['date'].max()
                    
                    # Convert Timestamps to strings
                    first_date_str = first_date.strftime('%Y-%m-%d')
                    last_date_str = last_date.strftime('%Y-%m-%d')
                    
                    # Update with actual processed data dates
                    stock_info[symbol]['processed_first_date'] = first_date_str
                    stock_info[symbol]['processed_last_date'] = last_date_str
                    
                    # If no IPO date was found, use first trading date from full historical data
                    if not stock_info[symbol].get('ipo_date') and stock_info[symbol].get('first_trading_date'):
                        stock_info[symbol]['ipo_date'] = stock_info[symbol]['first_trading_date']
                        stock_info[symbol]['listing_date'] = stock_info[symbol]['first_trading_date']
                        logger.info(f"Using first trading date as IPO for {symbol}: {stock_info[symbol]['first_trading_date']}")
                
                # Save data directly to database instead of CSV
                self.save_daily_data_to_database(daily_df, symbol)
            
        # Save stock metadata directly to database
        logger.info("Saving stock metadata to database:")
        self.save_stock_info_to_database(stock_info)
        
        logger.info("Data collection completed!")
        
        # Verify data was loaded correctly
        self.verify_database_data()


if __name__ == "__main__":
    # Database configuration - use Unix socket when running during container initialization
    DB_CONFIG = {
        "host": "/var/run/postgresql",  # Unix socket directory
        "database": os.getenv("DB_NAME", "simulated_trading_platform"),
        "user": os.getenv("DB_USER", "trading_user"), 
        "password": os.getenv("DB_PASSWORD", "trading_password"),
        # No port needed for Unix socket connection
    }
    
    # List of stocks to collect
    SYMBOLS = [
        # Large established companies
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "TSLA", "NVDA", "JPM", "V", "JNJ",
        "WMT", "PG", "UNH", "HD", "DIS",
        "MA", "BAC", "ADBE", "CRM", "NFLX",
        "X", "T", "QCOM", 
        
        # Recent IPOs
        "UBER", "LYFT", "ZM", "DOCU", "PTON", "SNOW", "ABNB",
        
        # Older companies with different IPO periods
        "IBM", "GE", "KO", "MMM", "XOM", "CVX",
        
        # ETFs (tradeable)
        "SPY", "QQQ", "IWM", "VTI", "VXUS",
        
        # Troubled stocks
        "GME", "AMC", "BB", "NOK"
    ]
    
    # Date range for historical data
    # Last 10 years
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=10*365)).strftime("%Y-%m-%d")
    
    # From 25 to 10 years ago (Combined 25 years of data)
    #END_DATE = (datetime.now()- timedelta(days=10*365)).strftime("%Y-%m-%d")
    #START_DATE = (datetime.now() - timedelta(days=25*365)).strftime("%Y-%m-%d")

    # From 40 to 25 years ago (Combined 40 years of data)
    #END_DATE = (datetime.now()- timedelta(days=25*365)).strftime("%Y-%m-%d")
    #START_DATE = (datetime.now() - timedelta(days=40*365)).strftime("%Y-%m-%d")
    
    print(f"Collecting data from {START_DATE} to {END_DATE}")
    
    # Create collector with database configuration
    collector = FreeDataCollector(DB_CONFIG)
    
    # Collect all data directly to database
    collector.collect_all_data(SYMBOLS, START_DATE, END_DATE)
    
    print("\nData collection complete!")