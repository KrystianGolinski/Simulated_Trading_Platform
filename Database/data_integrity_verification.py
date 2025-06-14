import pandas as pd
import os
import glob
from typing import Dict, List
import logging
from datetime import timedelta
from data_utils import get_date_column, is_intraday_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrityVerifier:
    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = data_dir
        self.daily_dir = os.path.join(data_dir, "daily", "cleaned")
        self.intraday_dir = os.path.join(data_dir, "intraday", "cleaned")
        self.test_results = []
    
    def _create_test_result(self, test_name: str, symbol: str, total_rows: int, invalid_rows: int, 
                           details: Dict = None, passed: bool = None) -> Dict:
        """Helper method to create standardized test result dictionaries"""
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
        """Test that OHLC relationships are valid (high >= open/close, low <= open/close)"""
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
        """
        Test that all prices are positive
        """
        test_name = f"Price Positivity - {symbol}"
        
        price_columns = ['open', 'high', 'low', 'close', 'adj_close']
        negative_prices = 0
        zero_prices = 0
        
        for col in price_columns:
            if col in df.columns:
                negative_prices += (df[col] < 0).sum()
                zero_prices += (df[col] == 0).sum()
        
        total_invalid = negative_prices + zero_prices
        total_price_values = len(df) * len([col for col in price_columns if col in df.columns])
        
        result = {
            'test_name': test_name,
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
        
        return result
    
    def test_volume_validity(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Test that volume is non-negative"""
        negative_volume = (df['volume'] < 0).sum()
        return self._create_test_result(
            f"Volume Validity - {symbol}", symbol, len(df), negative_volume,
            {'negative_volume': negative_volume}
        )
    
    def test_date_consistency(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Test date consistency and chronological order
        """
        test_name = f"Date Consistency - {symbol}"
        
        date_col = 'date' if 'date' in df.columns else 'datetime'
        df_sorted = df.copy()
        df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
        df_sorted = df_sorted.sort_values(date_col)
        
        # Check for duplicates
        duplicates = df_sorted.duplicated(subset=[date_col, 'symbol']).sum()
        
        # Check for missing dates (gaps > 7 days for daily, > 1 day for intraday)
        df_sorted['time_diff'] = df_sorted[date_col].diff()
        
        # Determine if intraday based on time component
        sample_date = df_sorted[date_col].iloc[0]
        is_intraday = sample_date.hour != 0 or sample_date.minute != 0 or sample_date.second != 0
        
        if is_intraday:
            # For intraday data, allow for weekend gaps (up to 4 days for long weekends)
            large_gaps = (df_sorted['time_diff'] > timedelta(days=4)).sum()
        else:
            # For daily data, allow up to 7 days for holidays
            large_gaps = (df_sorted['time_diff'] > timedelta(days=7)).sum()
        
        total_issues = duplicates + large_gaps
        total_rows = len(df)
        
        result = {
            'test_name': test_name,
            'symbol': symbol,
            'total_rows': total_rows,
            'invalid_rows': total_issues,
            'pass_rate': ((total_rows - total_issues) / total_rows) * 100,
            'passed': total_issues == 0,
            'details': {
                'duplicate_dates': duplicates,
                'large_gaps': large_gaps,
                'is_intraday': is_intraday
            }
        }
        
        return result
    
    def test_price_adjustments(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Test that adjusted close prices are reasonable compared to close prices
        """
        test_name = f"Price Adjustments - {symbol}"
        
        if 'adj_close' not in df.columns:
            return {
                'test_name': test_name,
                'symbol': symbol,
                'passed': True,
                'details': {'message': 'No adjusted close column found - skipping test'}
            }
        
        # Calculate adjustment ratio
        df['adj_ratio'] = df['adj_close'] / df['close']
        
        # Look for extreme adjustments (ratio < 0.1 or > 10)
        extreme_adjustments = ((df['adj_ratio'] < 0.1) | (df['adj_ratio'] > 10)).sum()
        
        # Look for negative adjustments
        negative_adjustments = (df['adj_ratio'] < 0).sum()
        
        total_issues = extreme_adjustments + negative_adjustments
        total_rows = len(df)
        
        result = {
            'test_name': test_name,
            'symbol': symbol,
            'total_rows': total_rows,
            'invalid_rows': total_issues,
            'pass_rate': ((total_rows - total_issues) / total_rows) * 100,
            'passed': total_issues == 0,
            'details': {
                'extreme_adjustments': extreme_adjustments,
                'negative_adjustments': negative_adjustments,
                'avg_adjustment_ratio': df['adj_ratio'].mean(),
                'min_adjustment_ratio': df['adj_ratio'].min(),
                'max_adjustment_ratio': df['adj_ratio'].max()
            }
        }
        
        return result
    
    def test_data_completeness(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Test for missing values in critical columns
        """
        test_name = f"Data Completeness - {symbol}"
        
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
        
        result = {
            'test_name': test_name,
            'symbol': symbol,
            'total_values': total_values,
            'missing_values': missing_values,
            'pass_rate': ((total_values - missing_values) / total_values) * 100 if total_values > 0 else 100,
            'passed': missing_values == 0,
            'details': column_details
        }
        
        return result
    
    def verify_file(self, file_path: str) -> List[Dict]:
        """
        Run all integrity tests on a single file
        """
        filename = os.path.basename(file_path)
        symbol = filename.split('_')[0]
        
        logger.info(f"Verifying data integrity for {filename}")
        
        try:
            df = pd.read_csv(file_path)
            
            # Run all tests
            test_results = [
                self.test_ohlc_relationships(df, symbol),
                self.test_price_positivity(df, symbol),
                self.test_volume_validity(df, symbol),
                self.test_date_consistency(df, symbol),
                self.test_price_adjustments(df, symbol),
                self.test_data_completeness(df, symbol)
            ]
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error verifying {filename}: {str(e)}")
            return [{
                'test_name': f"File Load Error - {symbol}",
                'symbol': symbol,
                'passed': False,
                'error': str(e)
            }]
    
    def verify_all_files(self, data_type: str = "daily") -> List[Dict]:
        """
        Verify all files in the specified directory
        """
        if data_type == "daily":
            source_dir = self.daily_dir
        elif data_type == "intraday":
            source_dir = self.intraday_dir
        else:
            raise ValueError("data_type must be 'daily' or 'intraday'")
        
        if not os.path.exists(source_dir):
            logger.error(f"Directory not found: {source_dir}")
            return []
        
        csv_files = glob.glob(os.path.join(source_dir, "*.csv"))
        all_results = []
        
        for file_path in csv_files:
            file_results = self.verify_file(file_path)
            all_results.extend(file_results)
        
        return all_results
    
    def print_verification_summary(self, results: List[Dict], data_type: str):
        """
        Print a summary of verification results
        """
        print(f"\n{'='*60}")
        print(f"DATA INTEGRITY VERIFICATION - {data_type.upper()} DATA")
        print(f"{'='*60}")
        
        # Group results by symbol
        symbols = list(set(result['symbol'] for result in results if 'symbol' in result))
        total_tests = len(results)
        passed_tests = sum(1 for result in results if result.get('passed', False))
        
        print(f"Total tests run: {total_tests}")
        print(f"Tests passed: {passed_tests}")
        print(f"Tests failed: {total_tests - passed_tests}")
        print(f"Overall pass rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Print results by symbol
        for symbol in sorted(symbols):
            symbol_results = [r for r in results if r.get('symbol') == symbol]
            symbol_passed = sum(1 for r in symbol_results if r.get('passed', False))
            
            print(f"{symbol}:")
            print(f"  Tests: {len(symbol_results)}/{len(symbol_results)} | Passed: {symbol_passed} | Failed: {len(symbol_results) - symbol_passed}")
            
            # Show failed tests
            failed_tests = [r for r in symbol_results if not r.get('passed', False)]
            if failed_tests:
                for test in failed_tests:
                    print(f"failed {test['test_name']}")
                    if 'details' in test:
                        for key, value in test['details'].items():
                            if value != 0:
                                print(f"       {key}: {value}")
            else:
                print(f"All tests passed")
            print()
        
        print(f"{'='*60}")
    
    def run_full_verification(self):
        """
        Run complete verification on both daily and intraday data
        """
        print("Starting data integrity verification...")
        
        # Verify daily data
        daily_results = self.verify_all_files("daily")
        if daily_results:
            self.print_verification_summary(daily_results, "daily")
        
        # Verify intraday data
        intraday_results = self.verify_all_files("intraday")
        if intraday_results:
            self.print_verification_summary(intraday_results, "intraday")
        
        # Overall summary
        all_results = daily_results + intraday_results
        if all_results:
            total_passed = sum(1 for r in all_results if r.get('passed', False))
            total_tests = len(all_results)
            
            print(f"\n{'='*60}")
            print("OVERALL VERIFICATION SUMMARY")
            print(f"{'='*60}")
            print(f"Total files verified: {len(set(r.get('symbol', '') for r in all_results))}")
            print(f"Total tests executed: {total_tests}")
            print(f"Overall pass rate: {(total_passed/total_tests)*100:.1f}%")
            
            if total_passed == total_tests:
                print("All tests passed!")
            else:
                print(f"{total_tests - total_passed} tests failed - review details above")
            
            print(f"{'='*60}")

if __name__ == "__main__":
    verifier = DataIntegrityVerifier()
    verifier.run_full_verification()