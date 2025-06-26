#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict
import os
import json
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreeDataCollector:
    
    # Simplified data collector with integrated data cleaning
    # Collects data from Yahoo Finance, cleans it, and saves cleaned CSV files
    
    def __init__(self):
        # Initialize data collector for CSV-only workflow with cleaning
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
    
    def save_to_file(self, df: pd.DataFrame, symbol: str, data_type: str = "daily"):
        # Save cleaned DataFrame to CSV file
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
        logger.info(f"Saved {len(df)} cleaned records to {filename}")
    
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
                # Clean the data before saving
                original_count = len(daily_df)
                daily_df = self.clean_data(daily_df)
                cleaned_count = len(daily_df)
                
                if cleaned_count < original_count:
                    logger.info(f"Cleaned {symbol}: {original_count} -> {cleaned_count} rows ({original_count - cleaned_count} removed)")
                
                self.save_to_file(daily_df, symbol, "daily")
            
            time.sleep(1)
        
        logger.info("Data collection completed!")
        
        # Generate summary
        self.generate_summary()
        
        # Run validation on all collected data
        self.validate_all_data()
    
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
    
    def validate_all_data(self):
        # Validate all collected data files
        logger.info("Running validation on all collected data...")
        
        daily_dir = os.path.join(self.data_dir, "daily")
        csv_files = glob.glob(os.path.join(daily_dir, "*.csv"))
        
        validation_results = []
        
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            symbol = filename.split('_')[0]
            
            try:
                df = pd.read_csv(file_path)
                
                # Run validation tests
                tests = [
                    self.test_ohlc_relationships(df, symbol),
                    self.test_price_positivity(df, symbol),
                    self.test_volume_validity(df, symbol),
                    self.test_data_completeness(df, symbol)
                ]
                
                validation_results.extend(tests)
                
            except Exception as e:
                logger.error(f"Error validating {filename}: {str(e)}")
        
        # Print validation summary
        self.print_validation_summary(validation_results)
    
    def test_ohlc_relationships(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that OHLC relationships are valid
        valid_high = (df['high'] >= df['open']) & (df['high'] >= df['close'])
        valid_low = (df['low'] <= df['open']) & (df['low'] <= df['close'])
        valid_range = df['high'] >= df['low']
        
        invalid_count = (~(valid_high & valid_low & valid_range)).sum()
        
        return {
            'test_name': f"OHLC Relationships - {symbol}",
            'symbol': symbol,
            'total_rows': len(df),
            'invalid_rows': invalid_count,
            'passed': invalid_count == 0
        }
    
    def test_price_positivity(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that all prices are positive
        price_columns = ['open', 'high', 'low', 'close', 'adj_close']
        invalid_count = 0
        
        for col in price_columns:
            if col in df.columns:
                invalid_count += (df[col] <= 0).sum()
        
        return {
            'test_name': f"Price Positivity - {symbol}",
            'symbol': symbol,
            'total_rows': len(df),
            'invalid_rows': invalid_count,
            'passed': invalid_count == 0
        }
    
    def test_volume_validity(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that volume is non-negative
        invalid_count = (df['volume'] < 0).sum()
        
        return {
            'test_name': f"Volume Validity - {symbol}",
            'symbol': symbol,
            'total_rows': len(df),
            'invalid_rows': invalid_count,
            'passed': invalid_count == 0
        }
    
    def test_data_completeness(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test for missing values in critical columns
        critical_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_count = 0
        
        for col in critical_columns:
            if col in df.columns:
                missing_count += df[col].isna().sum()
        
        return {
            'test_name': f"Data Completeness - {symbol}",
            'symbol': symbol,
            'total_rows': len(df),
            'invalid_rows': missing_count,
            'passed': missing_count == 0
        }
    
    def print_validation_summary(self, validation_results: List[Dict]):
        # Print validation summary
        print("\n" + "="*60)
        print("DATA VALIDATION SUMMARY")
        print("="*60)
        
        passed_tests = sum(1 for test in validation_results if test['passed'])
        total_tests = len(validation_results)
        
        print(f"Total validation tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in validation_results if not test['passed']]
        if failed_tests:
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['invalid_rows']} invalid rows")
        else:
            print("\nAll validation tests passed!")
        
        print("="*60)

if __name__ == "__main__":
    # List of stocks to collect
    SYMBOLS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "TSLA", "NVDA", "JPM", "V", "JNJ",
        "WMT", "PG", "UNH", "HD", "DIS",
        "MA", "BAC", "ADBE", "CRM", "NFLX",
        "X", "T","QCOM", "^SPX", "^NYA"
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
    print("Data will be saved to CSV files for import to database")
    
    # Create collector
    collector = FreeDataCollector()
    
    # Collect all data
    collector.collect_all_data(SYMBOLS, START_DATE, END_DATE)
    
    print("\nData collection complete!")