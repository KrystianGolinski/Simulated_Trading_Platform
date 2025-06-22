import pandas as pd
import os
import glob
from typing import Dict, List
import logging
from datetime import timedelta
from data_utils import get_date_column, is_intraday_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidator:
    #Comprehensive data validation and cleaning system
    #Combines data cleaning and integrity verification
    
    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = data_dir
        self.daily_dir = os.path.join(data_dir, "daily")
        self.intraday_dir = os.path.join(data_dir, "intraday")

    # Data cleaning methods
    def handle_stock_splits_and_dividends(self, df: pd.DataFrame) -> pd.DataFrame:
        # Handle stock splits and dividends by adjusting OHLCV data
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
        # Adjust for missing trading days and remove obvious gaps
        df = df.copy()
        
        date_col = get_date_column(df)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Check if this is intraday data
        is_intraday = is_intraday_data(df)
        
        if is_intraday:
            # For intraday data, remove records with gaps > 1 day
            df['time_diff'] = df[date_col].diff()
            df = df[(df['time_diff'] <= pd.Timedelta(days=1)) | (df['time_diff'].isna())]
            df = df.drop('time_diff', axis=1)
        else:
            # For daily data, handle missing trading days
            df['date_only'] = df[date_col].dt.date
            df = df.drop_duplicates(subset=['date_only', 'symbol'], keep='first')
            df = df.drop('date_only', axis=1)
        
        return df
    
    def normalize_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Normalize price data and validate OHLC relationships
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
        # Clean a single CSV file with all cleaning routines
        df = pd.read_csv(file_path)
        
        # Apply all cleaning routines
        df = self.handle_stock_splits_and_dividends(df)
        df = self.adjust_missing_trading_days(df)
        df = self.normalize_price_data(df)
        
        # Save cleaned data if output path provided
        if output_path:
            df.to_csv(output_path, index=False)
        
        return df
    
    # Data integrity validation
    def _create_test_result(self, test_name: str, symbol: str, total_rows: int, invalid_rows: int, 
                           details: Dict = None, passed: bool = None) -> Dict:
        # Helper method to create standardized test result dictionaries
        if passed is None:
            passed = invalid_rows == 0
            
        return {
            'test_name': test_name,
            'symbol': symbol,
            'total_rows': total_rows,
            'invalid_rows': invalid_rows,
            'pass_rate': ((total_rows - invalid_rows) / total_rows) * 100 if total_rows > 0 else 100,
            'passed': passed,
            'details': details or {}
        }
    
    def test_ohlc_relationships(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that OHLC relationships are valid
        valid_high = (df['high'] >= df['open']) & (df['high'] >= df['close'])
        valid_low = (df['low'] <= df['open']) & (df['low'] <= df['close'])
        valid_range = df['high'] >= df['low']
        
        invalid_high, invalid_low, invalid_range = (~valid_high).sum(), (~valid_low).sum(), (~valid_range).sum()
        
        return self._create_test_result(
            f"OHLC Relationships - {symbol}", symbol, len(df), 
            invalid_high + invalid_low + invalid_range,
            {'invalid_high': invalid_high, 'invalid_low': invalid_low, 'invalid_range': invalid_range}
        )
    
    def test_price_positivity(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that all prices are positive
        price_columns = ['open', 'high', 'low', 'close', 'adj_close']
        negative_prices = 0
        zero_prices = 0
        
        for col in price_columns:
            if col in df.columns:
                negative_prices += (df[col] < 0).sum()
                zero_prices += (df[col] == 0).sum()
        
        total_invalid = negative_prices + zero_prices
        total_price_values = len(df) * len([col for col in price_columns if col in df.columns])
        
        return {
            'test_name': f"Price Positivity - {symbol}",
            'symbol': symbol,
            'total_price_values': total_price_values,
            'invalid_values': total_invalid,
            'pass_rate': ((total_price_values - total_invalid) / total_price_values) * 100,
            'passed': total_invalid == 0,
            'details': {
                'negative_prices': negative_prices,
                'zero_prices': zero_prices
            }
        }
    
    def test_volume_validity(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test that volume is non-negative
        negative_volume = (df['volume'] < 0).sum()
        return self._create_test_result(
            f"Volume Validity - {symbol}", symbol, len(df), negative_volume,
            {'negative_volume': negative_volume}
        )
    
    def test_data_completeness(self, df: pd.DataFrame, symbol: str) -> Dict:
        # Test for missing values in critical columns
        critical_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_values = 0
        total_values = 0
        column_details = {}
        
        for col in critical_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                missing_values += missing_count
                total_values += len(df)
                column_details[col] = missing_count
        
        return {
            'test_name': f"Data Completeness - {symbol}",
            'symbol': symbol,
            'total_values': total_values,
            'missing_values': missing_values,
            'pass_rate': ((total_values - missing_values) / total_values) * 100 if total_values > 0 else 100,
            'passed': missing_values == 0,
            'details': column_details
        }

    # Combined Operations
    def clean_and_validate_file(self, file_path: str, output_path: str = None) -> Dict:
        # Clean a file and run integrity validation, returning combined results
        filename = os.path.basename(file_path)
        symbol = filename.split('_')[0]
        
        try:
            # Read and clean data
            original_df = pd.read_csv(file_path)
            cleaned_df = self.clean_csv_file(file_path, output_path)
            
            # Run validation tests on cleaned data
            validation_results = [
                self.test_ohlc_relationships(cleaned_df, symbol),
                self.test_price_positivity(cleaned_df, symbol),
                self.test_volume_validity(cleaned_df, symbol),
                self.test_data_completeness(cleaned_df, symbol)
            ]
            
            # Generate cleaning report
            cleaning_report = {
                'symbol': symbol,
                'original_rows': len(original_df),
                'cleaned_rows': len(cleaned_df),
                'rows_removed': len(original_df) - len(cleaned_df),
                'removal_percentage': ((len(original_df) - len(cleaned_df)) / len(original_df)) * 100,
                'validation_passed': all(test['passed'] for test in validation_results),
                'validation_results': validation_results
            }
            
            return cleaning_report
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'validation_passed': False
            }
    
    def process_all_files(self, data_type: str = "daily") -> Dict:
        # Process all files with cleaning and validation
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
        results = []
        
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            output_path = os.path.join(cleaned_dir, filename)
            
            result = self.clean_and_validate_file(file_path, output_path)
            results.append(result)
        
        # Print summary
        self.print_processing_summary(results, data_type)
        
        return {
            'data_type': data_type,
            'files_processed': len(results),
            'results': results
        }
    
    def print_processing_summary(self, results: list, data_type: str):
        # Print a summary of cleaning and validation
        print(f"\n{'='*60}")
        print(f"DATA PROCESSING SUMMARY - {data_type.upper()} DATA")
        print(f"{'='*60}")
        
        # Calculate totals
        successful_files = [r for r in results if 'error' not in r]
        total_original = sum(r.get('original_rows', 0) for r in successful_files)
        total_cleaned = sum(r.get('cleaned_rows', 0) for r in successful_files)
        total_removed = total_original - total_cleaned
        validation_passed = sum(1 for r in successful_files if r.get('validation_passed', False))
        
        print(f"Files processed: {len(results)}")
        print(f"Successful: {len(successful_files)}")
        print(f"Errors: {len(results) - len(successful_files)}")
        print(f"Validation passed: {validation_passed}/{len(successful_files)}")
        print()
        
        if successful_files:
            print(f"Total original rows: {total_original:,}")
            print(f"Total cleaned rows: {total_cleaned:,}")
            print(f"Total rows removed: {total_removed:,}")
            print(f"Overall removal rate: {(total_removed/total_original)*100:.2f}%")
            print()
            
            print("Per-file breakdown:")
            print(f"{'Symbol':<8} {'Original':<10} {'Cleaned':<10} {'Removed':<8} {'% Removed':<10} {'Valid':<6}")
            print("-" * 70)
            
            for result in sorted(successful_files, key=lambda x: x['symbol']):
                validation_status = "[PASS]" if result.get('validation_passed', False) else "[FAIL]"
                print(f"{result['symbol']:<8} {result['original_rows']:<10,} {result['cleaned_rows']:<10,} "
                      f"{result['rows_removed']:<8,} {result['removal_percentage']:<10.2f}% {validation_status:<6}")
        
        print(f"\n{'='*60}")

if __name__ == "__main__":
    # Initialize data validator
    validator = DataValidator()
    
    # Process daily data
    print("Processing daily data...")
    daily_results = validator.process_all_files("daily")
    
    # Process intraday data
    print("Processing intraday data...")
    intraday_results = validator.process_all_files("intraday")
    
    print("Data processing completed!")