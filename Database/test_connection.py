#!/usr/bin/env python3
import psycopg2

def test_database_connection():
    # Test PostgreSQL connection using various configurations
    
    configs = [
        {
            "name": "localhost",
            "host": "localhost",
            "database": "simulated_trading_platform",
            "user": "trading_user",
            "password": "trading_password",
            "port": 5433
        },
        {
            "name": "host.docker.internal (Windows Docker)",
            "host": "host.docker.internal",
            "database": "simulated_trading_platform",
            "user": "trading_user",
            "password": "trading_password",
            "port": 5433
        },
        {
            "name": "127.0.0.1 (Windows alternative)",
            "host": "127.0.0.1",
            "database": "simulated_trading_platform",
            "user": "trading_user",
            "password": "trading_password",
            "port": 5433
        },
        {
            "name": "Docker container IP",
            "host": "172.18.0.3",
            "database": "simulated_trading_platform",
            "user": "trading_user",
            "password": "trading_password",
            "port": 5433
        }
    ]
    
    for config in configs:
        print(f"\nTesting connection with {config['name']}...")
        try:
            conn = psycopg2.connect(
                host=config["host"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                port=config["port"]
            )
            print(f"Connection successful to {config['name']}!")
            
            # Test basic query
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"   PostgreSQL version: {version[0][:50]}...")
            
            cur.close()
            conn.close()
            return config  # Return successful config
            
        except Exception as e:
            print(f"Connection failed to {config['name']}: {e}")
    
    return None

if __name__ == "__main__":
    print("Testing PostgreSQL connection...")
    successful_config = test_database_connection()
    
    if successful_config:
        print(f"\nUse this configuration:")
        print(f"   host: '{successful_config['host']}'")
    else:
        print("\nAll connection attempts failed. Check:")