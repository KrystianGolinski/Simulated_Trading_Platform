#!/bin/bash

echo "Running Trading Platform Docker Setup..."

# Ensure all required directories exist
mkdir -p Backend/cpp-engine/include Backend/cpp-engine/src Frontend/trading-platform-ui

# Run the Docker setup
cd "$(dirname "$0")"
./Docker/docker-setup.sh