#!/bin/bash

# Setup script for Database Python environment
# This script creates a Python virtual environment and installs required packages

set -e  # Exit on any error

echo "Setting up Python environment for Database scripts:"

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation:"
else
    echo "Creating virtual environment:"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages with retry and resume support
echo "Installing required packages:"
pip install --retries 3 --timeout 30 -r requirements.txt

# Check if required Python scripts exist
if [ ! -f "DataGathering.py" ]; then
    echo "Error: DataGathering.py not found"
    exit 1
fi

if [ ! -f "CSVtoPostgres.py" ]; then
    echo "Error: CSVtoPostgres.py not found"
    exit 1
fi

echo "Running DataGathering.py..."
python DataGathering.py

if [ $? -eq 0 ]; then
    echo "DataGathering.py completed successfully"
    echo "Running CSVtoPostgres.py..."
    python CSVtoPostgres.py
    
    if [ $? -eq 0 ]; then
        echo "CSVtoPostgres.py completed successfully"
        echo "All tasks completed!"
    else
        echo "Error: CSVtoPostgres.py failed"
    fi
else
    echo "Error: DataGathering.py failed"
fi

# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated"