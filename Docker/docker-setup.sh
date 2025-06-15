#!/bin/bash

echo "Setting up Trading Platform Development Environment..."

# Change to project root directory
cd "$(dirname "$0")/.."

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
    cp Docker/.env.example .env
    echo "Please edit .env file with your configuration"
fi

# Build and start containers
echo "Building and starting containers..."
cd Docker
$COMPOSE_CMD -f docker-compose.dev.yml up --build -d

echo "Services available:"
echo "Frontend:    http://localhost:3000"
echo "FastAPI:     http://localhost:8000"
echo "API Docs:    http://localhost:8000/docs"
echo "PostgreSQL:  localhost:5432"
echo "Redis:       localhost:6379"
echo ""
echo "Commands:"
echo "Stop:     $COMPOSE_CMD -f Docker/docker-compose.dev.yml down"
echo "Logs:     $COMPOSE_CMD -f Docker/docker-compose.dev.yml logs -f [service]"