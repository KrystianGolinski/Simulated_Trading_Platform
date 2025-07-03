#!/usr/bin/env python3

# Database seeding script for reproducible test environments
# Creates consistent test data for integration testing

import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend API path for imports
backend_path = Path(__file__).parent.parent / "Backend" / "api"
sys.path.insert(0, str(backend_path))

class DatabaseSeeder:
    def __init__(self, db_path=None):
        # Initialize database seeder with optional custom database path
        if db_path is None:
            # Default to backend database path
            self.db_path = backend_path / "trading_data.db"
        else:
            self.db_path = Path(db_path)
        
        self.test_data_path = Path(__file__).parent
    
    def connect(self):
        # Create database connection
        return sqlite3.connect(str(self.db_path))
    
    def create_test_tables(self):
        # Create necessary tables for testing if they don't exist
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Create stocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    sector TEXT,
                    market_cap BIGINT
                )
            """)
            
            # Create daily_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    date DATE,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    FOREIGN KEY (symbol) REFERENCES stocks (symbol),
                    UNIQUE(symbol, date)
                )
            """)
            
            # Create simulations table for test results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_simulations (
                    simulation_id TEXT PRIMARY KEY,
                    config TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    results TEXT
                )
            """)
            
            conn.commit()
            print("Test database tables created/verified")
    
    def seed_test_stocks(self):
        # Seed test stock symbols
        test_stocks = [
            ("AAPL", "Apple Inc.", "Technology", 3000000000000),
            ("GOOGL", "Alphabet Inc.", "Technology", 2000000000000),
            ("MSFT", "Microsoft Corporation", "Technology", 2800000000000),
            ("TSLA", "Tesla Inc.", "Automotive", 800000000000),
            ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", 1500000000000),
            ("META", "Meta Platforms Inc.", "Technology", 800000000000),
            ("NVDA", "NVIDIA Corporation", "Technology", 1200000000000),
            ("AMD", "Advanced Micro Devices", "Technology", 250000000000),
            ("INTC", "Intel Corporation", "Technology", 200000000000),
            ("CRM", "Salesforce Inc.", "Technology", 250000000000)
        ]
        
        with self.connect() as conn:
            cursor = conn.cursor()
            
            for symbol, name, sector, market_cap in test_stocks:
                cursor.execute("""
                    INSERT OR REPLACE INTO stocks (symbol, name, sector, market_cap)
                    VALUES (?, ?, ?, ?)
                """, (symbol, name, sector, market_cap))
            
            conn.commit()
            print(f"Seeded {len(test_stocks)} test stock symbols")
    
    def generate_test_price_data(self, symbol, start_date, end_date, base_price=100):
        # Generate deterministic test price data for a symbol
        import random
        
        # Use symbol as seed for reproducible data
        random.seed(hash(symbol) % 1000000)
        
        prices = []
        current_date = start_date
        current_price = base_price
        
        while current_date <= end_date:
            # Skip weekends (basic simulation)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Generate realistic price movement
                daily_change = random.uniform(-0.05, 0.05)  # ±5% max daily change
                current_price *= (1 + daily_change)
                
                # Ensure price stays positive
                current_price = max(current_price, 1.0)
                
                # Generate OHLC data
                high = current_price * random.uniform(1.0, 1.03)
                low = current_price * random.uniform(0.97, 1.0)
                open_price = current_price * random.uniform(0.99, 1.01)
                close_price = current_price
                volume = random.randint(1000000, 50000000)
                
                prices.append({
                    'symbol': symbol,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
            
            current_date += timedelta(days=1)
        
        return prices
    
    def seed_test_price_data(self):
        # Seed test price data for all test stocks
        # Generate data for 2023 (full year for adequate testing)
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Base prices for different stocks (for variety)
        base_prices = {
            'AAPL': 150, 'GOOGL': 100, 'MSFT': 250, 'TSLA': 200, 'AMZN': 90,
            'META': 200, 'NVDA': 200, 'AMD': 80, 'INTC': 30, 'CRM': 150
        }
        
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Clear existing test data
            cursor.execute("DELETE FROM daily_data WHERE date BETWEEN ? AND ?",
                         (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            total_records = 0
            for symbol, base_price in base_prices.items():
                prices = self.generate_test_price_data(symbol, start_date, end_date, base_price)
                
                for price in prices:
                    cursor.execute("""
                        INSERT OR REPLACE INTO daily_data 
                        (symbol, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (price['symbol'], price['date'], price['open'], 
                         price['high'], price['low'], price['close'], price['volume']))
                
                total_records += len(prices)
                print(f"Generated {len(prices)} records for {symbol}")
            
            conn.commit()
            print(f"Total test price records seeded: {total_records}")
    
    def seed_test_simulations(self):
        # Seed sample test simulation records
        test_simulations = [
            {
                'simulation_id': 'test_sim_001',
                'config': json.dumps({
                    'symbols': ['AAPL'],
                    'start_date': '2023-01-01',
                    'end_date': '2023-01-31',
                    'starting_capital': 10000,
                    'strategy': 'ma_crossover'
                }),
                'status': 'completed',
                'created_at': '2023-01-01 00:00:00',
                'completed_at': '2023-01-01 00:05:00',
                'results': json.dumps({
                    'ending_value': 10250,
                    'total_return_pct': 2.5,
                    'total_trades': 4
                })
            },
            {
                'simulation_id': 'test_sim_002',
                'config': json.dumps({
                    'symbols': ['GOOGL', 'MSFT'],
                    'start_date': '2023-01-01',
                    'end_date': '2023-03-31',
                    'starting_capital': 25000,
                    'strategy': 'ma_crossover'
                }),
                'status': 'completed',
                'created_at': '2023-01-01 01:00:00',
                'completed_at': '2023-01-01 01:15:00',
                'results': json.dumps({
                    'ending_value': 26750,
                    'total_return_pct': 7.0,
                    'total_trades': 12
                })
            }
        ]
        
        with self.connect() as conn:
            cursor = conn.cursor()
            
            for sim in test_simulations:
                cursor.execute("""
                    INSERT OR REPLACE INTO test_simulations 
                    (simulation_id, config, status, created_at, completed_at, results)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sim['simulation_id'], sim['config'], sim['status'],
                     sim['created_at'], sim['completed_at'], sim['results']))
            
            conn.commit()
            print(f"Seeded {len(test_simulations)} test simulation records")
    
    def cleanup_test_data(self):
        # Clean up test data (for isolation between test runs)
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Clean up test simulations
            cursor.execute("DELETE FROM test_simulations")

            conn.commit()
            print("Test data cleanup completed")
    
    def verify_seeded_data(self):
        # Verify that seeded data is consistent and accessible
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Check stocks
            cursor.execute("SELECT COUNT(*) FROM stocks")
            stock_count = cursor.fetchone()[0]
            
            # Check price data
            cursor.execute("SELECT COUNT(*) FROM daily_data WHERE date >= '2023-01-01'")
            price_count = cursor.fetchone()[0]
            
            # Check test simulations
            cursor.execute("SELECT COUNT(*) FROM test_simulations")
            sim_count = cursor.fetchone()[0]
            
            print(f"Verification complete:")
            print(f"  - Stocks: {stock_count}")
            print(f"  - Price records: {price_count}")
            print(f"  - Test simulations: {sim_count}")
            
            return {
                'stocks': stock_count,
                'price_records': price_count,
                'test_simulations': sim_count
            }
    
    def seed_all(self):
        # Run complete database seeding process
        print("Starting database seeding for test environment:")
        
        try:
            self.create_test_tables()
            self.seed_test_stocks()
            self.seed_test_price_data()
            self.seed_test_simulations()
            stats = self.verify_seeded_data()
            
            print("\n[PASS] Database seeding completed successfully!")
            print("Test environment is ready for integration testing.")
            return stats
            
        except Exception as e:
            print(f"\n[FAIL] Database seeding failed: {e}")
            sys.exit(1)

def main():
    # Command line interface for database seeding
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed database with test data')
    parser.add_argument('--db-path', help='Custom database path')
    parser.add_argument('--cleanup-only', action='store_true', 
                       help='Only clean up test data')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify existing data')
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder(args.db_path)
    
    if args.cleanup_only:
        seeder.cleanup_test_data()
    elif args.verify_only:
        seeder.verify_seeded_data()
    else:
        seeder.seed_all()

if __name__ == "__main__":
    main()