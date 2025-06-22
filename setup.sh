#!/bin/bash

set -e  # Exit on any error

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
        echo ""
        echo "To install on Ubuntu/Debian:"
        echo "sudo apt-get update"
        echo "sudo apt-get install build-essential cmake nodejs npm docker.io docker-compose"
        echo ""
        echo "Don't forget to add your user to docker group:"
        echo "sudo usermod -aG docker \$USER"
        echo "Then log out and back in."
        exit 1
    fi
    
    print_success "All dependencies found"
}

# Function to check Docker permissions
check_docker_permissions() {
    print_status "Checking Docker permissions..."
    
    if ! docker info &> /dev/null; then
        print_error "Cannot connect to Docker daemon"
        echo ""
        echo "This usually means:"
        echo "1. Docker is not running: sudo systemctl start docker"
        echo "2. Permission denied: sudo usermod -aG docker \$USER (then logout/login)"
        echo "3. Docker service not installed properly"
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
    
    # Run tests
    print_status "Running C++ unit tests..."
    if [ -f "build/test_basic" ]; then
        ./build/test_basic
        if [ $? -eq 0 ]; then
            print_success "C++ unit tests passed"
        else
            print_error "C++ unit tests failed"
            exit 1
        fi
    else
        print_warning "C++ tests not found"
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
    
    # Wait a moment for services to start
    sleep 3
    
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
run_development_mode() {
    print_status "Starting development mode..."
    
    echo ""
    echo "Trading Platform Setup Complete!"
    echo ""
    echo "Services Available:"
    echo "  Frontend:    http://localhost:3000"
    echo "  FastAPI:     http://localhost:8000"
    echo "  API Docs:    http://localhost:8000/docs"
    echo "  PostgreSQL:  localhost:5433"
}

# Main execution flow
main() {
    check_docker_environment
    check_dependencies
    check_docker_permissions
    setup_environment
    build_cpp_engine
    setup_frontend
    setup_docker_services
    run_development_mode
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
    --help)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no option)     Full setup - C++, Frontend, and Docker"
        echo "  --cpp-only      Build C++ engine only"
        echo "  --frontend-only Setup frontend only"
        echo "  --docker-only   Setup Docker services only"
        echo "  --help          Show this help"
        ;;
    *)
        main
        ;;
esac