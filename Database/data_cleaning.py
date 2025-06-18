import pandas as pd
import os
import glob
from typing import Dict
import logging
from data_utils import get_date_column, is_intraday_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = data_dir
        self.daily_dir = os.path.join(data_dir, "daily")
        self.intraday_dir = os.path.join(data_dir, "intraday")
        
    def handle_stock_splits_and_dividends(self, df: pd.DataFrame) -> pd.DataFrame:
        # Handle stock splits and dividends by detecting and adjusting for them.
        # Uses the ratio between close and adj_close to identify corporate actions.

        df = df.copy()
        
        date_col = get_date_column(df)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Calculate adjustment factor from close vs adj_close
        df['adj_factor'] = df['adj_close'] / df['close']
        
        # Find significant changes in adjustment factor (potential splits/dividends)
        df['adj_factor_change'] = df['adj_factor'].pct_change()
        
        # Identify corporate actions (change > 1% in adjustment factor)
        corporate_actions = df[abs(df['adj_factor_change']) > 0.01]
        
        if not corporate_actions.empty:
            logger.info(f"Found {len(corporate_actions)} potential corporate actions")
            
            # Apply adjustments to OHLCV data to match adj_close
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col] * df['adj_factor']
            
            # Adjust volume inversely for splits
            df['volume'] = df['volume'] / df['adj_factor']
            
        # Remove helper columns
        df = df.drop(['adj_factor', 'adj_factor_change'], axis=1)
        
        return df
    
    def adjust_missing_trading_days(self, df: pd.DataFrame) -> pd.DataFrame:
        # Adjust for missing trading days by identifying and handling gaps in trading data.
        # For intraday data, this focuses on identifying missing trading sessions.
        # For daily data, this handles weekends and holidays.
        
        df = df.copy()
        
        date_col = get_date_column(df)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Check if this is intraday data
        is_intraday = is_intraday_data(df)
        
        if is_intraday:
            # For intraday data, just remove obvious gaps (more than 1 day between consecutive records)
            df['time_diff'] = df[date_col].diff()
            # Remove records with gaps > 1 day (likely data quality issues)
            df = df[(df['time_diff'] <= pd.Timedelta(days=1)) | (df['time_diff'].isna())]
            df = df.drop('time_diff', axis=1)
        else:
            # For daily data, handle missing trading days
            df['date_only'] = df[date_col].dt.date
            df = df.drop_duplicates(subset=['date_only', 'symbol'], keep='first')
            df = df.drop('date_only', axis=1)
        
        return df
    
    def normalize_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Normalize price data by:
        # 1. Ensuring consistent decimal precision
        # 2. Removing any negative prices or volumes
        # 3. Validating OHLC relationships
        
        df = df.copy()
        
        # Round price columns to 4 decimal places
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
        date_col = 'date' if 'date' in df.columns else 'datetime'
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        return df
    
    def clean_csv_file(self, file_path: str, output_path: str = None) -> pd.DataFrame:
        # Clean a single CSV file with all cleaning routines.
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Apply all cleaning routines
        df = self.handle_stock_splits_and_dividends(df)
        df = self.adjust_missing_trading_days(df)
        df = self.normalize_price_data(df)
        
        # Save cleaned data if output path provided
        if output_path:
            df.to_csv(output_path, index=False)
        
        return df
    
    def clean_all_files(self, data_type: str = "daily") -> Dict[str, pd.DataFrame]:
        # Clean all CSV files in the specified directory (daily or intraday).

        if data_type == "daily":
            source_dir = self.daily_dir
        elif data_type == "intraday":
            source_dir = self.intraday_dir
        else:
            raise ValueError("data_type must be 'daily' or 'intraday'")
        
        # Create cleaned directory
        cleaned_dir = os.path.join(source_dir, "cleaned")
        os.makedirs(cleaned_dir, exist_ok=True)
        
        # Get all CSV files
        csv_files = glob.glob(os.path.join(source_dir, "*.csv"))
        cleaned_data = {}
        cleaning_reports = []
        
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            output_path = os.path.join(cleaned_dir, filename)
            
            try:
                # Read original data for comparison
                original_df = pd.read_csv(file_path)
                
                # Clean the data
                cleaned_df = self.clean_csv_file(file_path, output_path)
                cleaned_data[filename] = cleaned_df
                
                # Generate cleaning report
                symbol = filename.split('_')[0]  # Extract symbol from filename
                report = self.generate_cleaning_report(original_df, cleaned_df, symbol)
                cleaning_reports.append(report)
            except Exception as e:
                logger.error(f"Error cleaning {filename}: {str(e)}")
        
        # Print cleaning reports
        self.print_cleaning_summary(cleaning_reports, data_type)
        
        return cleaned_data
    
    def generate_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame, symbol: str) -> Dict:
        # Generate a report comparing original and cleaned data.
        
        report = {
            'symbol': symbol,
            'original_rows': len(original_df),
            'cleaned_rows': len(cleaned_df),
            'rows_removed': len(original_df) - len(cleaned_df),
            'removal_percentage': ((len(original_df) - len(cleaned_df)) / len(original_df)) * 100,
            'date_range': {
                'start': cleaned_df['date'].min() if 'date' in cleaned_df.columns else cleaned_df['datetime'].min(),
                'end': cleaned_df['date'].max() if 'date' in cleaned_df.columns else cleaned_df['datetime'].max()
            }
        }
        
        return report
    
    def print_cleaning_summary(self, reports: list, data_type: str):
        # Print a summary of all cleaning operations.
        
        print(f"\n{'='*50}")
        print(f"CLEANING SUMMARY - {data_type.upper()} DATA")
        print(f"{'='*50}")
        
        total_original = sum(report['original_rows'] for report in reports)
        total_cleaned = sum(report['cleaned_rows'] for report in reports)
        total_removed = total_original - total_cleaned
        
        print(f"Files processed: {len(reports)}")
        print(f"Total original rows: {total_original:,}")
        print(f"Total cleaned rows: {total_cleaned:,}")
        print(f"Total rows removed: {total_removed:,}")
        print(f"Overall removal rate: {(total_removed/total_original)*100:.2f}%")
        print()
        
        print("Per-stock breakdown:")
        print(f"{'Symbol':<8} {'Original':<10} {'Cleaned':<10} {'Removed':<10} {'% Removed':<10}")
        print("-" * 60)
        
        for report in sorted(reports, key=lambda x: x['symbol']):
            print(f"{report['symbol']:<8} {report['original_rows']:<10,} {report['cleaned_rows']:<10,} "
                  f"{report['rows_removed']:<10,} {report['removal_percentage']:<10.2f}%")
        
        print(f"\n{'='*50}")

if __name__ == "__main__":
    # Initialize data cleaner
    cleaner = DataCleaner()
    
    # Clean daily data
    print("Cleaning daily data...")
    daily_cleaned = cleaner.clean_all_files("daily")
    
    # Clean intraday data
    print("Cleaning intraday data...")
    intraday_cleaned = cleaner.clean_all_files("intraday")
    
    print("Data cleaning completed!")