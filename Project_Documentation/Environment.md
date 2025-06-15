# Development Environment Setup - Complete Guide

This document outlines the complete development environment setup for the Simulated Trading Platform, including all components and their configurations.

## Overview

The trading platform consists of multiple services working together:
- **C++ Engine**: High-performance trading simulation core
- **FastAPI Backend**: Python API bridge between frontend and C++ engine
- **React Frontend**: TypeScript-based user interface
- **PostgreSQL + TimescaleDB**: Time-series database for historical data
- **Redis**: Caching layer for performance optimization

## Environment Setup Completed

### C++ Development Environment

**Location**: `Backend/cpp-engine/`

**Components Set Up**:
- CMake build system with C++17 standard
- Proper directory structure (`src/`, `include/`, `build/`)
- Basic main.cpp executable for testing
- Dockerfile for containerized builds

**Build Configuration**:
```cmake
cmake_minimum_required(VERSION 3.16)
project(TradingEngine VERSION 1.0.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
```

### Python Virtual Environment & FastAPI

**Location**: `Backend/api/`

**Components Set Up**:
- Python 3.10 virtual environment
- FastAPI application with CORS middleware
- Essential dependencies installed:
  - `fastapi==0.104.1`
  - `uvicorn[standard]==0.24.0`
  - `pydantic==2.5.0`
  - `psycopg2-binary==2.9.9` (PostgreSQL adapter)
  - `redis==5.0.1`
  - `pybind11==2.11.1` (C++ binding)

**API Endpoints**:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - Auto-generated API documentation

**Access**: http://localhost:8000

### React Frontend with TypeScript

**Location**: `Frontend/trading-platform-ui/`

**Components Set Up**:
- React 18 with TypeScript template
- Essential dependencies:
  - `axios` for API communication
  - `chart.js` and `react-chartjs-2` for data visualization
  - Tailwind CSS framework (configured but not active due to compatibility)

**Access**: http://localhost:3000

### Docker Development Containers

**Configuration Files**:
- `Docker/docker-compose.dev.yml` - Development environment
- `Docker/docker-compose.yml` - Production environment  
- `Docker/docker-setup.sh` - Automated setup script
- `Docker/.env.example` - Environment template
- Individual Dockerfiles for each service
- `setup.sh` - Root-level convenience script

**Services Configured**:

1. **PostgreSQL + TimescaleDB**:
   - Image: `timescale/timescaledb:latest-pg15`
   - Port: 5432
   - Database: `trading_platform`
   - User: `trader`

2. **Redis**:
   - Image: `redis:7-alpine`
   - Port: 6379
   - Persistent volume for data

3. **FastAPI**:
   - Custom build from `Backend/api/`
   - Port: 8000
   - Hot reload enabled for development

4. **React Frontend**:
   - Multi-stage Dockerfile (development/production)
   - Port: 3000
   - File watching enabled

5. **C++ Engine**:
   - Custom build with Ubuntu 22.04 base
   - CMake and build tools included

**Network Configuration**:
- Custom bridge network: `trading_network`
- All services can communicate internally
- External access via mapped ports

## Setup Instructions

### Prerequisites
- Docker and Docker Compose V2
- Git (already configured)

## Testing & Verification

All components have been tested and verified working:

### C++ Engine
- Compiles without errors
- Executable runs successfully
- CMake build system functional

### FastAPI Backend  
- All dependencies install correctly
- Application starts without errors
- API endpoints accessible
- Auto-documentation generated

### React Frontend
- TypeScript compilation successful
- Production build completes
- Development server starts correctly

### Docker Integration
- All containers build successfully
- Services communicate properly
- Port mapping works correctly
- Volume persistence configured

## Next Steps

The development environment is now fully configured and ready for implementing the core trading platform features. The next phase involves:

1. Database schema creation
2. Historical data loading
3. Core simulation engine development
4. API endpoint implementation
5. Frontend component development

All foundational infrastructure is in place to support rapid development of the trading simulation features.

## Troubleshooting

**Docker Permission Issues**:
```bash
sudo usermod -aG docker $USER
# Log out and back in, or use sudo with docker commands
```

**Port Conflicts**:
- Check if ports 3000, 8000, 5432, or 6379 are in use
- Modify port mappings in docker-compose files if needed

**Build Failures**:
- Check Docker daemon is running
- Verify all required files are present
- Review container logs for specific error messages