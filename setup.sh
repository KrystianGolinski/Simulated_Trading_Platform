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

# Function to setup Node.js environment
setup_nodejs_environment() {
    # Source NVM if available to ensure we use the correct Node.js version
    if [ -f "$HOME/.nvm/nvm.sh" ]; then
        print_status "Loading NVM environment..."
        source "$HOME/.nvm/nvm.sh"
        
        # Use the latest/default Node.js version from NVM
        if command -v nvm &> /dev/null; then
            nvm use default &> /dev/null || nvm use node &> /dev/null || true
        fi
    fi
    
    # Check if we now have a modern Node.js version
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        
        if [ "$NODE_MAJOR" -lt 14 ]; then
            print_warning "Node.js version $NODE_VERSION is outdated (minimum v14 required)"
            print_warning "Consider updating Node.js to avoid dependency warnings"
        else
            print_status "Using Node.js version $NODE_VERSION"
        fi
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking system dependencies:"
    
    # Setup Node.js environment first
    setup_nodejs_environment
    
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
    print_status "Checking Docker permissions:"
    
    if ! docker info &> /dev/null; then
        print_error "Cannot connect to Docker daemon"
        exit 1
    fi
    
    print_success "Docker permissions OK"
}

# Function to build C++ engine
build_cpp_engine() {
    print_status "Building C++ Trading Engine:"
    
    if [ ! -d "Backend/cpp-engine" ]; then
        print_error "C++ engine directory not found"
        exit 1
    fi
    
    cd Backend/cpp-engine
    
    # Check if already built and up to date
    if [ -f "build/trading_engine" ] && [ -f "build/test_comprehensive" ]; then
        # Check if source files are newer than binaries
        if [ "$(find src include -name '*.cpp' -o -name '*.h' -newer build/trading_engine | wc -l)" -eq 0 ]; then
            print_status "C++ engine is already up to date, skipping build"
            cd ../..
            return 0
        fi
        print_status "Source files changed, rebuilding C++ engine"
    fi
    
    # Run the build script
    if [ -f "build.sh" ]; then
        chmod +x build.sh
        ./build.sh
        
        # Verify build success
        if [ ! -f "build/trading_engine" ]; then
            print_error "C++ engine build failed - executable not found"
            exit 1
        fi
    else
        # Fallback: manual build
        mkdir -p build
        cd build
        
        # Clean previous build if CMakeCache exists but is stale
        if [ -f "CMakeCache.txt" ]; then
            if [ "../CMakeLists.txt" -nt "CMakeCache.txt" ]; then
                print_status "CMakeLists.txt changed, cleaning build cache"
                rm -f CMakeCache.txt
            fi
        fi
        
        cmake .. || { print_error "CMake configuration failed"; exit 1; }
        make -j$(nproc) || { print_error "Make build failed"; exit 1; }
        cd ..
        
        # Verify build success
        if [ ! -f "build/trading_engine" ]; then
            print_error "C++ engine build failed - executable not found"
            exit 1
        fi
    fi
    
    cd ../..
    print_success "C++ engine built successfully"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up Frontend:"
    
    # Ensure we have the correct Node.js environment
    setup_nodejs_environment
    
    if [ ! -d "Frontend/trading-platform-ui" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    cd Frontend/trading-platform-ui
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in frontend directory"
        exit 1
    fi
    
    # Install dependencies with improved logic
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies:"
        npm install --silent || { print_error "npm install failed"; exit 1; }
    else
        # Check if package.json is newer than node_modules
        if [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
            print_status "Package files changed, updating npm dependencies:"
            npm install --silent || { print_error "npm install failed"; exit 1; }
        else
            print_status "npm dependencies are up to date"
        fi
    fi
    
    # Verify critical dependencies are available
    if [ ! -d "node_modules/react" ]; then
        print_error "React not found in node_modules, dependency installation may have failed"
        exit 1
    fi
    
    cd ../..
    print_success "Frontend setup complete"
}

# Function to setup Python API dependencies
setup_api_dependencies() {
    print_status "Setting up Python API dependencies:"
    
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
        print_status "Creating Python virtual environment:"
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
    print_status "Checking Python dependencies in virtual environment:"
    
    # Check if dependencies need to be installed or updated
    deps_missing=false
    deps_outdated=false
    
    # Check if requirements.txt is newer than the last pip install
    if [ -f "requirements.txt" ]; then
        if [ "requirements.txt" -nt "venv/pyvenv.cfg" ]; then
            deps_outdated=true
            print_status "requirements.txt has been updated"
        fi
    fi
    
    # Check each package individually (some have different import names)
    if ! python -c "import fastapi" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import uvicorn" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import pydantic" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import asyncpg" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import pytest" 2>/dev/null; then deps_missing=true; fi
    if ! python -c "import httpx" 2>/dev/null; then deps_missing=true; fi
    
    if [ "$deps_missing" = true ] || [ "$deps_outdated" = true ]; then
        if [ "$deps_missing" = true ]; then
            print_status "Installing missing Python dependencies in virtual environment:"
        else
            print_status "Updating Python dependencies in virtual environment:"
        fi
        
        python -m pip install -r requirements.txt -q --disable-pip-version-check
        
        if [ $? -eq 0 ]; then
            print_success "Python dependencies installed successfully in virtual environment"
            # Touch venv config to update timestamp for future checks
            touch venv/pyvenv.cfg
        else
            print_error "Failed to install Python dependencies"
            exit 1
        fi
    else
        print_success "Python dependencies are up to date in virtual environment"
    fi
    
    # Deactivate virtual environment
    deactivate
    
    cd ../..
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment:"
    
    # Ensure all required directories exist
    mkdir -p Backend/cpp-engine/{include,src,tests,build}
    mkdir -p Backend/api
    mkdir -p Frontend/trading-platform-ui
    mkdir -p Project_Documentation
    
    # Create .env file
    if [ ! -f .env ]; then
        print_status "Creating .env file from template:"
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        # Check if .env.example is newer than .env (template updated)
        if [ -f .env.example ] && [ ".env.example" -nt ".env" ]; then
            print_warning ".env.example has been updated since .env was created"
            print_warning "Please review .env.example for new configuration options"
            print_warning "Consider updating your .env file manually"
        else
            print_status ".env file already exists and is up to date"
        fi
    fi
    
    # Validate .env file has required variables
    if [ -f .env ]; then
        print_status "Validating .env file:"
        required_vars=("DB_HOST" "DB_USER" "DB_PASSWORD" "TEST_DB_HOST" "TEST_DB_USER" "TEST_DB_PASSWORD")
        missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^${var}=" .env; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -ne 0 ]; then
            print_warning "Missing required variables in .env: ${missing_vars[*]}"
            print_warning "Please add these variables to your .env file"
        else
            print_success "All required environment variables are present"
        fi
    fi
    
    print_success "Environment setup complete"
}

# Function to wait for database readiness
wait_for_database() {
    print_status "Waiting for database to be ready:"
    
    # Load database credentials from .env with validation
    if [ -f ".env" ]; then
        TEST_DB_HOST=$(grep "^TEST_DB_HOST=" .env | cut -d'=' -f2)
        TEST_DB_PORT=$(grep "^TEST_DB_PORT=" .env | cut -d'=' -f2)
        TEST_DB_USER=$(grep "^TEST_DB_USER=" .env | cut -d'=' -f2)
        TEST_DB_NAME=$(grep "^TEST_DB_NAME=" .env | cut -d'=' -f2)
        
        # Use defaults if values are empty
        TEST_DB_HOST=${TEST_DB_HOST:-localhost}
        TEST_DB_PORT=${TEST_DB_PORT:-5433}
        TEST_DB_USER=${TEST_DB_USER:-trading_user}
        TEST_DB_NAME=${TEST_DB_NAME:-simulated_trading_platform}
    else
        TEST_DB_HOST=localhost
        TEST_DB_PORT=5433
        TEST_DB_USER=trading_user
        TEST_DB_NAME=simulated_trading_platform
    fi
    
    print_status "Checking database at ${TEST_DB_HOST}:${TEST_DB_PORT}/${TEST_DB_NAME}"
    
    # Wait for PostgreSQL to accept connections
    MAX_ATTEMPTS=30
    ATTEMPT=1
    
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        # Use pg_isready
        if command -v pg_isready &> /dev/null; then
            if pg_isready -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" &> /dev/null; then
                print_success "Database is ready!"
                return 0
            fi
        else
            # Fallback if pg_isready not available: try docker exec
            if docker ps --format "{{.Names}}" | grep -q "trading-db"; then
                if docker exec trading-db pg_isready -U "$TEST_DB_USER" -d "$TEST_DB_NAME" &> /dev/null 2>&1; then
                    print_success "Database is ready!"
                    return 0
                fi
            else
                print_error "Database healtcheck failed"
                exit 1
            fi
        fi
        
        if [ $ATTEMPT -eq 1 ]; then
            print_status "Database not ready yet, waiting:"
        fi
        
        if [ $((ATTEMPT % 5)) -eq 0 ]; then
            print_status "Still waiting for database (attempt $ATTEMPT/$MAX_ATTEMPTS):"
        fi
        
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    print_error "Database failed to become ready after $MAX_ATTEMPTS attempts"
    print_error "Attempted connection to: ${TEST_DB_HOST}:${TEST_DB_PORT}/${TEST_DB_NAME}"
    
    # Show diagnostic information
    print_status "Diagnostic information:"
    if docker ps --format "{{.Names}}" | grep -q "trading-db"; then
        echo "  - Database container 'trading-db' is running"
        docker logs --tail 10 trading-db 2>/dev/null | sed 's/^/    /'
    else
        echo "  - Database container 'trading-db' is not running"
    fi
    
    exit 1
}

# Function to run tests
run_cpp_tests() {
    print_status "Running C++ test suite:"
    
    if [ ! -f "Backend/cpp-engine/build/test_comprehensive" ]; then
        print_error "C++ test suite not found. Build the C++ engine first."
        exit 1
    fi
    
    # Verify test executable is executable
    if [ ! -x "Backend/cpp-engine/build/test_comprehensive" ]; then
        print_error "C++ test executable is not executable"
        exit 1
    fi
    
    cd Backend/cpp-engine
    
    # Load local testing credentials from .env file with validation
    if [ -f "../../.env" ]; then
        # Extract TEST_DB_* variables from .env and set as DB_* for the test
        DB_HOST_VAL=$(grep "^TEST_DB_HOST=" ../../.env | cut -d'=' -f2)
        DB_PORT_VAL=$(grep "^TEST_DB_PORT=" ../../.env | cut -d'=' -f2)
        DB_NAME_VAL=$(grep "^TEST_DB_NAME=" ../../.env | cut -d'=' -f2)
        DB_USER_VAL=$(grep "^TEST_DB_USER=" ../../.env | cut -d'=' -f2)
        DB_PASSWORD_VAL=$(grep "^TEST_DB_PASSWORD=" ../../.env | cut -d'=' -f2)
        
        # Validate that we got values
        if [ -n "$DB_HOST_VAL" ] && [ -n "$DB_PORT_VAL" ] && [ -n "$DB_NAME_VAL" ] && [ -n "$DB_USER_VAL" ]; then
            export DB_HOST="$DB_HOST_VAL"
            export DB_PORT="$DB_PORT_VAL"
            export DB_NAME="$DB_NAME_VAL"
            export DB_USER="$DB_USER_VAL"
            export DB_PASSWORD="$DB_PASSWORD_VAL"
            print_status "Using database configuration from .env file"
        else
            print_warning "Incomplete database configuration in .env file, using defaults"
            export DB_HOST=localhost
            export DB_PORT=5433
            export DB_NAME=simulated_trading_platform
            export DB_USER=trading_user
            export DB_PASSWORD=trading_password
        fi
    else
        print_warning "No .env file found, using default test configuration"
        export DB_HOST=localhost
        export DB_PORT=5433
        export DB_NAME=simulated_trading_platform
        export DB_USER=trading_user
        export DB_PASSWORD=trading_password
    fi
    
    # Run tests with timeout to prevent hanging
    print_status "Running tests with configuration: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    timeout 300 ./build/test_comprehensive
    test_result=$?
    
    if [ $test_result -eq 0 ]; then
        print_success "[PASS] C++ tests"
    elif [ $test_result -eq 124 ]; then
        print_error "[TIMEOUT] C++ tests timed out after 5 minutes"
        exit 1
    else
        print_error "[FAIL] C++ tests (exit code: $test_result)"
        exit 1
    fi
    
    cd ../..
}

# Function to run API tests
run_api_tests() {
    print_status "Running API test suite:"
    
    if [ ! -f "Backend/api/tests/run_comprehensive_tests.py" ]; then
        print_error "API test suite not found"
        exit 1
    fi
    
    cd Backend/api
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found - cannot run API tests"
        exit 1
    fi
    
    # Check if virtual environment exists and is valid
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run setup first."
        exit 1
    fi
    
    if [ ! -f "venv/bin/activate" ]; then
        print_error "Virtual environment appears corrupted. Run setup again."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Verify Python in venv works
    if ! python --version &> /dev/null; then
        print_error "Python in virtual environment is not working"
        deactivate
        exit 1
    fi
    
    # Set testing mode environment variable
    export TESTING=true
    
    # Verify test script is executable
    if [ ! -r "tests/run_comprehensive_tests.py" ]; then
        print_error "Test script is not readable"
        deactivate
        exit 1
    fi
    
    # Run the API test suite with timeout
    print_status "Running API tests with timeout (10 minutes):"
    timeout 600 python tests/run_comprehensive_tests.py
    test_result=$?
    
    # Unset testing mode
    unset TESTING
    
    # Deactivate virtual environment
    deactivate
    
    if [ $test_result -eq 0 ]; then
        print_success "[PASS] API tests"
    elif [ $test_result -eq 124 ]; then
        print_error "[TIMEOUT] API tests timed out after 10 minutes"
        exit 1
    else
        print_error "[FAIL] API tests (exit code: $test_result)"
        exit 1
    fi
    
    cd ../..
}

# Function to setup Docker services
setup_docker_services() {
    print_status "Setting up Docker services:"
    
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
    
    # Check if docker-compose.dev.yml exists
    if [ ! -f "Docker/docker-compose.dev.yml" ]; then
        print_error "Docker compose file not found: Docker/docker-compose.dev.yml"
        exit 1
    fi
    
    # Check if services are already running
    if $COMPOSE_CMD -f Docker/docker-compose.dev.yml ps | grep -q "Up"; then
        print_status "Docker services are already running"
        
        # Check if we need to rebuild (Dockerfile changes)
        if [ "Backend/cpp-engine/Dockerfile" -nt "$($COMPOSE_CMD -f Docker/docker-compose.dev.yml images -q cpp-engine 2>/dev/null | head -1)" ] 2>/dev/null; then
            print_status "Dockerfile changes detected, rebuilding containers:"
            $COMPOSE_CMD -f Docker/docker-compose.dev.yml up --build -d
        else
            print_status "Containers are up to date"
        fi
    else
        # Build and start containers
        print_status "Building and starting containers:"
        $COMPOSE_CMD -f Docker/docker-compose.dev.yml up --build -d
        
        if [ $? -ne 0 ]; then
            print_error "Failed to start Docker services"
            print_error "Check logs with: $COMPOSE_CMD -f Docker/docker-compose.dev.yml logs"
            exit 1
        fi
    fi
    
    # Wait for database to be ready
    wait_for_database
    
    # Check if services are running with detailed status
    print_status "Checking service health:"
    
    # Get container status
    container_status=$($COMPOSE_CMD -f Docker/docker-compose.dev.yml ps --format "table {{.Service}}\t{{.State}}" | tail -n +2)
    
    # Check if services are running
    if echo "$container_status" | grep -q "running"; then
        print_success "Docker services started successfully"
    else
        print_error "Some services are not running properly"
        echo "Service Status:"
        echo "$container_status" | while read line; do
            echo "  $line"
        done
        print_error "Check logs with: $COMPOSE_CMD -f Docker/docker-compose.dev.yml logs"
        exit 1
    fi
}

# Function to verify setup completion
verify_setup() {
    print_status "Verifying setup completion:"
    
    local setup_issues=()
    
    # Check C++ engine
    if [ ! -f "Backend/cpp-engine/build/trading_engine" ]; then
        setup_issues+=("C++ engine executable not found")
    fi
    
    if [ ! -f "Backend/cpp-engine/build/test_comprehensive" ]; then
        setup_issues+=("C++ test executable not found")
    fi
    
    # Check frontend
    if [ ! -d "Frontend/trading-platform-ui/node_modules" ]; then
        setup_issues+=("Frontend dependencies not installed")
    fi
    
    # Check API
    if [ ! -d "Backend/api/venv" ]; then
        setup_issues+=("Python virtual environment not found")
    fi
    
    # Check environment file
    if [ ! -f ".env" ]; then
        setup_issues+=(".env file not found")
    fi
    
    # Check Docker services
    COMPOSE_CMD=""
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    fi
    
    if [ -n "$COMPOSE_CMD" ] && [ -f "Docker/docker-compose.dev.yml" ]; then
        # Check if services are running
        running_services=$($COMPOSE_CMD -f Docker/docker-compose.dev.yml ps --services --filter "status=running" 2>/dev/null | wc -l)
        if [ "$running_services" -eq 0 ]; then
            # Fallback check with original method
            if ! $COMPOSE_CMD -f Docker/docker-compose.dev.yml ps 2>/dev/null | grep -q -E "(Up|running)"; then
                setup_issues+=("Docker services not running")
            fi
        fi
    fi
    
    if [ ${#setup_issues[@]} -eq 0 ]; then
        print_success "Setup verification passed - all components are ready"
        return 0
    else
        print_warning "Setup verification found issues:"
        for issue in "${setup_issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    fi
}

# Function to show completion summary
run_confirmation() {
    echo ""
    
    # Run verification
    if verify_setup; then
        print_status "Trading Platform Setup Completed Successfully"
        print_status "Services Available:"
        print_status "Frontend: http://localhost:3000"
    else
        print_error "Setup completed with issues - please review and re-run if needed"
        exit 1
    fi
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
        print_status "Building C++ engine only:"
        build_cpp_engine
        ;;
    --frontend-only)
        print_status "Setting up frontend only:"
        setup_frontend
        ;;
    --docker-only)
        print_status "Setting up Docker services only:"
        check_docker_permissions
        setup_environment
        setup_docker_services
        ;;
    --api-only)
        print_status "Setting up API dependencies only:"
        setup_api_dependencies
        ;;
    --tests-only)
        print_status "Running test suites only:"
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
        echo "  --tests-only    Run test suites only"
        echo "  --help          Show this help"
        ;;
    *)
        main
        ;;
esac