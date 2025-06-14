#!/bin/bash

# Setup script for FastAPI development environment
# Run this script after installing python3-venv package

echo "Setting up Python virtual environment for FastAPI..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Virtual environment setup complete!"
echo "To activate: source venv/bin/activate"
echo "To run the API: python main.py"