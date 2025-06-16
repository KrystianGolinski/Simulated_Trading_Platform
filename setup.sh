#!/bin/bash

echo "Running Trading Platform Docker Setup..."

# Change to script directory (project root)
cd "$(dirname "$0")"

# Ensure all required directories exist
mkdir -p Backend/cpp-engine/include Backend/cpp-engine/src Frontend/trading-platform-ui

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Build and start containers (run from project root with .env file)
echo "Building and starting containers..."
$COMPOSE_CMD -f Docker/docker-compose.dev.yml up --build -d

echo ""
echo "Services available:"
echo "Frontend:    http://localhost:3000"
echo "FastAPI:     http://localhost:8000"
echo "API Docs:    http://localhost:8000/docs"
echo "PostgreSQL:  localhost:5433"
echo "Redis:       localhost:6379"
echo ""
echo "Commands:"
echo "Stop:     $COMPOSE_CMD -f Docker/docker-compose.dev.yml down"
echo "Logs:     $COMPOSE_CMD -f Docker/docker-compose.dev.yml logs -f [service]"
echo "Shell:    $COMPOSE_CMD -f Docker/docker-compose.dev.yml exec [service] sh"