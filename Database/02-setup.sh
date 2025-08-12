#!/bin/bash

# Setup script for Database initialization
# This script runs the data gathering process that populates the database directly

set -e  # Exit on any error

echo "Setting up database with stock market data:"

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Virtual environment is already created and activated via Dockerfile
# Verify required packages are installed
echo "Verifying Python packages are available:"
python3 -c "import pandas, psycopg2, yfinance" || {
    echo "Error: Required Python packages not found"
    exit 1
}

# Check if required Python script exists
if [ ! -f "DataGathering.py" ]; then
    echo "Error: DataGathering.py not found"
    exit 1
fi

echo "Running DataGathering.py to populate database (schema already created by 01-init.sql)..."
python DataGathering.py

if [ $? -eq 0 ]; then
    echo "DataGathering.py completed successfully"
    echo "Database populated with stock market data!"
else
    echo "Error: DataGathering.py failed"
    exit 1
fi

echo "Database setup completed successfully"