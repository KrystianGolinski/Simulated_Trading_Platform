#!/bin/bash

set -e  # Exit on any error
set -u  # Exit on unset variables
set -o pipefail  # Fail if any command in a pipeline fails

echo "Trading Platform Complete Setup"

# Change to script directory (project root)
cd "$(dirname "$0")"

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running in Docker environment
check_docker_environment() {
    if [ -f /.dockerenv ]; then
        print_error "This script should not be run inside a Docker container"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking system dependencies..."
    
    # Check for required tools
    local missing_tools=()
    
    # Check C++ build tools
    if ! command -v cmake &> /dev/null; then
        missing_tools+=("cmake")
    fi
    
    if ! command -v make &> /dev/null; then
        missing_tools+=("make")
    fi
    
    if ! command -v g++ &> /dev/null; then
        missing_tools+=("g++")
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    fi
    
    if ! command -v npm &> /dev/null; then
        missing_tools+=("npm")
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    print_success "All dependencies found"
}

# Function to check Docker permissions
check_docker_permissions() {
    print_status "Checking Docker permissions..."
    
    if ! docker info &> /dev/null; then
        print_error "Cannot connect to Docker daemon"
        exit 1
    fi
    
    print_success "Docker permissions OK"
}

# Function to build C++ engine
build_cpp_engine() {
    print_status "Building C++ Trading Engine..."
    
    if [ ! -d "Backend/cpp-engine" ]; then
        print_error "C++ engine directory not found"
        exit 1
    fi
    
    cd Backend/cpp-engine
    
    # Run the build script
    if [ -f "build.sh" ]; then
        chmod +x build.sh
        ./build.sh
    else
        # Fallback: manual build
        mkdir -p build
        cd build
        cmake ..
        make -j$(nproc)
        cd ..
    fi
    
    cd ../..
    print_success "C++ engine built successfully"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up Frontend..."
    
    if [ ! -d "Frontend/trading-platform-ui" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    cd Frontend/trading-platform-ui
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies..."
        npm install
    else
        print_status "npm dependencies already installed"
    fi
    
    cd ../..
    print_success "Frontend setup complete"
}

# Function to setup Python API dependencies
setup_api_dependencies() {
    print_status "Setting up Python API dependencies..."
    
    if [ ! -d "Backend/api" ]; then
        print_error "API directory not found"
        exit 1
    fi
    
    cd Backend/api
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
        
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip in virtual environment
    python -m pip install --upgrade pip -q --disable-pip-version-check
    
    # Check if dependencies are already installed in venv
    print_status "Checking Python dependencies in virtual environment..."
    
    # Check if all required packages are available
    deps_missing=false
    
    # Check each package individually (some have different import names)
    if ! python -c "import fastapi" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import uvicorn" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import pydantic" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import asyncpg" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import pytest" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import httpx" 2>/dev/null; then deps_missing=true; fi
    
    if [ "$deps_missing" = true ]; then
        print_status "Installing missing Python dependencies in virtual environment..."
        python -m pip install -r requirements.txt -q --disable-pip-version-check
        
        if [ $? -eq 0 ]; then
            print_success "Python dependencies installed successfully in virtual environment"
        else
            print_error "Failed to install Python dependencies"
            exit 1
        fi
    else
        print_success "Python dependencies already available in virtual environment"
    fi
    
    # Deactivate virtual environment
    deactivate
    
    cd ../..
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Ensure all required directories exist
    mkdir -p Backend/cpp-engine/{include,src,tests,build}
    mkdir -p Backend/api
    mkdir -p Frontend/trading-platform-ui
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status ".env file already exists"
    fi
    
    print_success "Environment setup complete"
}

# Function to wait for database readiness
wait_for_database() {
    print_status "Waiting for database to be ready..."
    
    # Load database credentials from .env
    if [ -f ".env" ]; then
        TEST_DB_HOST=$(grep "^TEST_DB_HOST=" .env | cut -d'=' -f2)
        TEST_DB_PORT=$(grep "^TEST_DB_PORT=" .env | cut -d'=' -f2)
        TEST_DB_USER=$(grep "^TEST_DB_USER=" .env | cut -d'=' -f2)
        TEST_DB_NAME=$(grep "^TEST_DB_NAME=" .env | cut -d'=' -f2)
    else
        TEST_DB_HOST=localhost
        TEST_DB_PORT=5433
        TEST_DB_USER=trading_user
        TEST_DB_NAME=simulated_trading_platform
    fi
    
    # Wait for PostgreSQL to accept connections
    MAX_ATTEMPTS=30
    ATTEMPT=1
    
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        if command -v pg_isready &> /dev/null; then
            # Use pg_isready if available
            if pg_isready -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" &> /dev/null; then
                print_success "Database is ready!"
                return 0
            fi
        else
            # Fallback: try to connect with docker exec
            if docker exec trading-db pg_isready -U "$TEST_DB_USER" -d "$TEST_DB_NAME" &> /dev/null; then
                print_success "Database is ready!"
                return 0
            fi
        fi
        
        print_status "Database not ready yet (attempt $ATTEMPT/$MAX_ATTEMPTS), waiting 2 seconds..."
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    print_error "Database failed to become ready after $MAX_ATTEMPTS attempts"
    exit 1
}

# Function to run comprehensive tests
run_cpp_tests() {
    print_status "Running C++ comprehensive test suite..."
    
    if [ ! -f "Backend/cpp-engine/build/test_comprehensive" ]; then
        print_error "C++ comprehensive test suite not found. Build the C++ engine first."
        exit 1
    fi
    
    cd Backend/cpp-engine
    
    # Load local testing credentials from .env file
    if [ -f "../../.env" ]; then
        # Extract TEST_DB_* variables from .env and set as DB_* for the test
        export DB_HOST=$(grep "^TEST_DB_HOST=" ../../.env | cut -d'=' -f2)
        export DB_PORT=$(grep "^TEST_DB_PORT=" ../../.env | cut -d'=' -f2)
        export DB_NAME=$(grep "^TEST_DB_NAME=" ../../.env | cut -d'=' -f2)
        export DB_USER=$(grep "^TEST_DB_USER=" ../../.env | cut -d'=' -f2)
        export DB_PASSWORD=$(grep "^TEST_DB_PASSWORD=" ../../.env | cut -d'=' -f2)
    else
        print_warning "No .env file found, using default test configuration"
        export DB_HOST=localhost
        export DB_PORT=5433
        export DB_NAME=simulated_trading_platform
        export DB_USER=trading_user
        export DB_PASSWORD=trading_password
    fi
    
    ./build/test_comprehensive
    if [ $? -eq 0 ]; then
        print_success "[PASS] C++ comprehensive tests"
    else
        print_error "[FAIL] C++ comprehensive tests"
        exit 1
    fi
    
    cd ../..
}

# Function to run comprehensive API tests
run_api_tests() {
    print_status "Running comprehensive API test suite..."
    
    if [ ! -f "Backend/api/tests/run_comprehensive_tests.py" ]; then
        print_error "API comprehensive test suite not found"
        exit 1
    fi
    
    cd Backend/api
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found - cannot run API tests"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run setup first."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set testing mode environment variable
    export TESTING=true
    
    # Run the comprehensive API test suite using venv python
    python tests/run_comprehensive_tests.py
    if [ $? -eq 0 ]; then
        print_success "API comprehensive tests"
    else
        print_error "API comprehensive tests"
        exit 1
    fi
    
    # Unset testing mode
    unset TESTING
    
    # Deactivate virtual environment
    deactivate
    
    cd ../..
}

# Function to setup Docker services
setup_docker_services() {
    print_status "Setting up Docker services..."
    
    # Check for Docker Compose
    COMPOSE_CMD=""
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Build and start containers
    print_status "Building and starting containers..."
    $COMPOSE_CMD -f Docker/docker-compose.dev.yml up --build -d
    
    # Wait for database to be ready
    wait_for_database
    
    # Check if services are running
    print_status "Checking service health..."
    
    # Check if containers are running
    if $COMPOSE_CMD -f Docker/docker-compose.dev.yml ps | grep -q "Up"; then
        print_success "Docker services started successfully"
    else
        print_warning "Some services may not be running. Check logs with:"
        echo "$COMPOSE_CMD -f Docker/docker-compose.dev.yml logs"
    fi
}

# Function to run development mode
run_confirmation() {
    echo ""
    print_status "Trading Platform Setup Complete!"
    print_status "Services Available:"
    print_status "Frontend: http://localhost:3000"
}

# Main execution flow
main() {
    check_docker_environment
    check_dependencies
    check_docker_permissions
    setup_environment
    build_cpp_engine
    setup_frontend
    setup_api_dependencies
    setup_docker_services
    run_cpp_tests
    run_api_tests
    run_confirmation
}

# Handle script arguments
case "${1:-}" in
    --cpp-only)
        print_status "Building C++ engine only..."
        build_cpp_engine
        ;;
    --frontend-only)
        print_status "Setting up frontend only..."
        setup_frontend
        ;;
    --docker-only)
        print_status "Setting up Docker services only..."
        check_docker_permissions
        setup_environment
        setup_docker_services
        ;;
    --api-only)
        print_status "Setting up API dependencies only..."
        setup_api_dependencies
        ;;
    --tests-only)
        print_status "Running comprehensive test suites only..."
        check_docker_permissions
        setup_api_dependencies
        wait_for_database
        run_cpp_tests
        run_api_tests
        ;;
    --help)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no option)     Full setup - C++, Frontend, API, Docker, and Tests"
        echo "  --cpp-only      Build C++ engine only"
        echo "  --frontend-only Setup frontend only"
        echo "  --api-only      Setup API dependencies only"
        echo "  --docker-only   Setup Docker services only"
        echo "  --tests-only    Run comprehensive test suites only"
        echo "  --help          Show this help"
        ;;
    *)
        main
        ;;
esac