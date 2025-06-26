#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
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
    
    # Simplified data collector
    # Collects data from Yahoo Finance, saves to CSV files
    
    def __init__(self):
        # Initialize data collector for CSV-only workflow
        self.data_dir = "historical_data"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "daily"), exist_ok=True)

    def fetch_stock_info(self, symbols: List[str]) -> Dict[str, Dict]:
        # Fetch stock metadata from Yahoo Finance
        stock_info = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                stock_info[symbol] = {
                    'name': info.get('longName', info.get('shortName', '')),
                    'sector': info.get('sector', ''),
                    'exchange': info.get('exchange', ''),
                    'currency': info.get('currency', 'USD'),
                    'market_cap': info.get('marketCap', 0)
                }
                
                logger.info(f"Fetched info for {symbol}")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching info for {symbol}: {e}")
                stock_info[symbol] = {
                    'name': symbol,
                    'sector': 'Unknown',
                    'exchange': 'Unknown'
                }
        
        return stock_info
    
    def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Fetch daily OHLCV data from Yahoo Finance
        # Args:
        #    symbol: Stock symbol
        #    start_date: Start date (YYYY-MM-DD)
        #    end_date: End date (YYYY-MM-DD)
        # Returns:
        #    DataFrame with OHLCV data
        
        try:
            df = yf.download(
                symbol, 
                start=start_date, 
                end=end_date,
                progress=False,
                auto_adjust=False  # Keep both 'close' and 'adjusted close'
            )
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Fix for MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Reset index to have date as a column
            df.reset_index(inplace=True)
            df['symbol'] = symbol
            
            # Rename columns to match schema
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            logger.info(f"Fetched {len(df)} daily records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return pd.DataFrame()
    
    def save_to_file(self, df: pd.DataFrame, symbol: str, data_type: str = "daily"):
        # Save DataFrame to CSV file
        if df.empty:
            return
            
        filename = os.path.join(self.data_dir, data_type, f"{symbol}_{data_type}.csv")
        
        # If file exists, append only new data
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename, parse_dates=['date' if data_type == 'daily' else 'datetime'])
            df = pd.concat([existing_df, df]).drop_duplicates(
                subset=['date' if data_type == 'daily' else 'datetime', 'symbol'],
                keep='last'
            ).sort_values('date' if data_type == 'daily' else 'datetime')
        
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(df)} records to {filename}")
    
    def collect_all_data(self, symbols: List[str], start_date: str, end_date: str):
        # Collect all available data for given symbols
        # Args:
        #    symbols: List of stock symbols
        #    start_date: Start date for daily data (YYYY-MM-DD)
        #    end_date: End date for daily data (YYYY-MM-DD)

        # First, get stock info
        logger.info("Fetching stock information...")
        stock_info = self.fetch_stock_info(symbols)
        
        # Save stock info
        with open(os.path.join(self.data_dir, "stock_info.json"), 'w') as f:
            json.dump(stock_info, f, indent=2)

        # Collect daily data for each symbol
        logger.info("Collecting daily historical data...")
        for symbol in symbols:
            logger.info(f"Processing {symbol}...")
            
            # Fetch daily data
            daily_df = self.fetch_daily_data(symbol, start_date, end_date)
            
            if not daily_df.empty:
                self.save_to_file(daily_df, symbol, "daily")
            
            time.sleep(1)
        
        logger.info("Data collection completed!")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        # Generate a summary of collected CSV data.
        summary = {"daily": {}}
        
        # Check daily files
        daily_dir = os.path.join(self.data_dir, "daily")
        if os.path.exists(daily_dir):
            for file in os.listdir(daily_dir):
                if file.endswith(".csv"):
                    df = pd.read_csv(os.path.join(daily_dir, file))
                    symbol = file.replace("_daily.csv", "")
                    summary["daily"][symbol] = {
                        "records": len(df),
                        "start_date": df['date'].min(),
                        "end_date": df['date'].max()
                    }
    
        # Save summary
        with open(os.path.join(self.data_dir, "summary.json"), 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\nData Collection Summary")
        print(f"Daily data collected for {len(summary['daily'])} symbols")
        
        for symbol, info in summary['daily'].items():
            print(f"\n{symbol}:")
            print(f"  Daily records: {info['records']}")
            print(f"  Date range: {info['start_date']} to {info['end_date']}")

if __name__ == "__main__":
    # List of stocks to collect
    SYMBOLS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "TSLA", "NVDA", "JPM", "V", "JNJ",
        "WMT", "PG", "UNH", "HD", "DIS",
        "MA", "BAC", "ADBE", "CRM", "NFLX",
        "X", "T","QCOM", "^SPX", "^NYA"
    ]
    
    # Date range for historical data (10 years)
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=10*365)).strftime("%Y-%m-%d")
    
    print(f"Collecting data from {START_DATE} to {END_DATE}")
    print("Data will be saved to CSV files for import to database")
    
    # Create collector (always saves to CSV files)
    collector = FreeDataCollector()
    
    # Collect all data
    collector.collect_all_data(SYMBOLS, START_DATE, END_DATE)
    
    print("\nData collection complete!")