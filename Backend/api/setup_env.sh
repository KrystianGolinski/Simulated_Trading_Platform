#!/bin/bash

# Setup script for FastAPI development environment
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