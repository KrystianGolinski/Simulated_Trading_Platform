#!/bin/bash

echo "Setting up Trading Platform Development Environment with Docker..."

# Debug: Show current working directory
echo "DEBUG: Current directory: $(pwd)"
echo "DEBUG: Script location: $0"
echo "DEBUG: Script directory: $(dirname "$0")"

# Always change to project root directory (parent of script's directory)
cd "$(dirname "$0")/.."

# Debug: Show new working directory
echo "DEBUG: After cd, current directory: $(pwd)"
echo "DEBUG: Backend directory exists: $(ls -la | grep Backend || echo 'NOT FOUND')"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose (V2 or V1)
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "Using Docker Compose V2"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "Using Docker Compose V1"
else
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp Docker/.env.example .env
    echo "Please edit .env file with your configuration before running docker-compose"
fi

# Build and start development containers
echo "Building and starting development containers..."
echo "DEBUG: About to run from Docker folder: $COMPOSE_CMD -f docker-compose.dev.yml up --build -d"
cd Docker
$COMPOSE_CMD -f docker-compose.dev.yml up --build -d

echo "Development environment started!"
echo "Services:"
echo "  - Frontend: http://localhost:3000"
echo "  - FastAPI: http://localhost:8000"
echo "  - FastAPI Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"

echo ""
echo "To stop all services: $COMPOSE_CMD -f Docker/docker-compose.dev.yml down"
echo "To view logs: $COMPOSE_CMD -f Docker/docker-compose.dev.yml logs -f [service_name]"