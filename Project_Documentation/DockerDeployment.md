# Docker Deployment Technical Documentation

## 1. Introduction

This document provides comprehensive technical documentation for the Docker-based containerization and orchestration of the Simulated Trading Platform. It covers container architecture, service orchestration, deployment strategies, and operational management.

**Container Orchestration:** Docker Compose with multi-service coordination  
**Base Images:** Ubuntu 22.04, Node 20 Alpine, TimescaleDB PostgreSQL 15, Python 3.10  
**Network Architecture:** Isolated bridge networks with inter-service communication  
**Volume Management:** Named volumes with persistent data storage  
**Health Monitoring:** Comprehensive health checks with automated recovery  

### 1.1. Core Design Principles

The containerization strategy emphasizes scalability, maintainability, and operational excellence:

- **Service Isolation**: Each component runs in dedicated containers with minimal dependencies
- **Multi-stage Builds**: Optimized image sizes with separate build and runtime stages
- **Health Monitoring**: Comprehensive health checks with configurable retry logic
- **Environment Configuration**: Externalized configuration via environment variables
- **Volume Management**: Persistent data storage with named volumes and bind mounts
- **Network Security**: Isolated networks with controlled inter-service communication
- **Resource Management**: Defined resource limits and dependencies
- **Development/Production Parity**: Consistent environments across development and production

### 1.2. Container Architecture Overview

#### Service Components
- **trading-db**: TimescaleDB database with automated schema initialization
- **trading-engine**: C++ trading engine with shared volume binary deployment
- **trading-api**: FastAPI application with database and engine integration
- **trading-ui**: React frontend with development and production configurations

#### Infrastructure Components
- **Named Volumes**: `postgres_data`, `cpp_engine_shared` for persistent storage
- **Networks**: `trading_network` for secure inter-service communication
- **Health Checks**: Service-level monitoring with dependency management
- **Environment Variables**: Centralized configuration via `.env` file

## 2. Service Architecture

### 2.1. Database Service (trading-db)

**Base Image**: `timescale/timescaledb:latest-pg15`  
**Container Name**: `trading-db`  
**Purpose**: TimescaleDB with automated schema initialization and data loading

#### Dockerfile Features
```dockerfile
# Custom TimescaleDB with Python3 for initialization
FROM timescale/timescaledb:latest-pg15

# Alpine package management for Python3 installation
RUN apk add --no-cache python3 py3-pip python3-dev && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt
```

#### Service Configuration
- **Port Mapping**: `5433:5432` (external:internal)
- **Volume**: `postgres_data:/var/lib/postgresql/data`
- **Environment**: Database credentials and configuration
- **Health Check**: Combined connectivity and data validation
  ```bash
  pg_isready -U trading_user -d simulated_trading_platform && \
  psql -U trading_user -d simulated_trading_platform -c 'SELECT COUNT(*) FROM stocks;'
  ```

#### Initialization Process
1. **Schema Creation**: `01-init.sql` creates tables, indexes, and functions
2. **Data Loading**: Automated stock data population via Python scripts
3. **Health Validation**: Ensures data presence before dependent services start

### 2.2. C++ Trading Engine Service (trading-engine)

**Base Image**: Multi-stage build from `ubuntu:22.04`  
**Container Name**: `trading-engine`  
**Purpose**: High-performance trading simulation engine with shared binary deployment

#### Multi-stage Build Process
```dockerfile
# Build stage - Full development environment
FROM ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y build-essential cmake libpq-dev nlohmann-json3-dev

# Runtime stage - Minimal runtime environment  
FROM ubuntu:22.04 AS runtime
RUN apt-get update && apt-get install -y libpq5 curl
COPY --from=builder /app/build/trading_engine /app/build/trading_engine
```

#### Service Configuration
- **Shared Volume**: `cpp_engine_shared:/shared` for binary distribution
- **Database Connection**: Environment-based PostgreSQL configuration
- **Health Check**: Binary availability validation
- **Command**: Binary deployment and service persistence

#### Binary Deployment Strategy
```bash
mkdir -p /shared && \
cp /app/build/trading_engine /shared/ && \
chmod +x /shared/trading_engine && \
tail -f /dev/null  # Keep container running
```

### 2.3. FastAPI Service (trading-api)

**Base Image**: `python:3.10-slim`  
**Container Name**: `trading-api`  
**Purpose**: REST API with database integration and C++ engine coordination

#### Dockerfile Configuration
```dockerfile
FROM python:3.10-slim
RUN apt-get install libpq-dev gcc curl
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
```

#### Service Dependencies
- **Database**: Waits for `trading-db` healthy status
- **Engine**: Waits for `trading-engine` healthy status  
- **Shared Volume**: Access to C++ engine binary via `cpp_engine_shared:/shared`
- **Port Mapping**: `8000:8000` for API access

#### Development vs Production
- **Development**: Volume mount with hot reload via uvicorn
- **Production**: Optimized WSGI server configuration

### 2.4. React Frontend Service (trading-ui)

**Multi-target Dockerfile**: Separate development and production stages  
**Container Name**: `trading-ui`  
**Purpose**: React TypeScript frontend with optimized production deployment

#### Production Build Stage
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 3000
```

#### Development Configuration
- **Hot Reload**: File watching with `CHOKIDAR_USEPOLLING=true`
- **Volume Mount**: Live code updates without rebuild
- **Port**: `3000:3000` for development server

#### Production Optimization
- **Nginx Server**: Static file serving with reverse proxy on port 80
- **Build Optimization**: `NODE_OPTIONS="--max-old-space-size=4096"`
- **Asset Caching**: Optimized nginx configuration
- **Port Mapping**: Production service runs on port 80 internally

## 3. Docker Compose Configuration

### 3.1. Service Orchestration

#### Development Environment (docker-compose.dev.yml)
```yaml
services:
  postgres:
    build: ../Database
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready && psql -c 'SELECT COUNT(*) FROM stocks;'"]
      
  cpp-engine:
    build: ../Backend/cpp-engine
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
        
  fastapi:
    build: ../Backend/api
    restart: unless-stopped
    depends_on:
      postgres: { condition: service_healthy }
      cpp-engine: { condition: service_healthy }
    command: ["python", "-m", "uvicorn", "main:app", "--reload"]
    
  frontend:
    build:
      target: development
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - CHOKIDAR_USEPOLLING=true
```

#### Production Environment (docker-compose.yml)
```yaml
services:
  postgres:
    restart: unless-stopped
  cpp-engine:
    restart: unless-stopped
  fastapi:
    restart: unless-stopped
  frontend:
    build:
      target: production
    restart: unless-stopped
    ports:
      - "80:80"  # Standard HTTP port for production
```

### 3.2. Network Configuration

#### Isolated Network Architecture
```yaml
networks:
  trading_network:
    driver: bridge
```

**Network Features:**
- **Service Isolation**: All services on dedicated network
- **DNS Resolution**: Services accessible by container name
- **Port Control**: Only necessary ports exposed to host
- **Security**: No direct external access to internal services

### 3.3. Volume Management

#### Named Volumes
```yaml
volumes:
  postgres_data:    # Database persistence
  cpp_engine_shared: # Binary sharing between services
```

#### Volume Usage Patterns
- **Database Persistence**: Critical data survives container restarts
- **Binary Sharing**: Efficient C++ engine distribution
- **Development Mounts**: Live code updates during development

## 4. Health Check Strategy

### 4.1. Multi-level Health Monitoring

#### Database Health Check
```bash
# Connectivity + Data Validation
pg_isready -U trading_user -d simulated_trading_platform && \
psql -U trading_user -d simulated_trading_platform -c 'SELECT COUNT(*) FROM stocks;' | grep -q '[0-9]'
```

#### API Health Check  
```bash
# HTTP endpoint validation
curl -f http://localhost:8000/health || exit 1
```

#### Engine Health Check
```bash
# Binary availability and functionality
test -x /shared/trading_engine
```

#### Frontend Health Check
```bash
# Server availability
wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1
```

### 4.2. Health Check Configuration

#### Timing Parameters
- **Interval**: `15s-30s` between checks
- **Timeout**: `10s` maximum check duration  
- **Retries**: `3-10` attempts before failure
- **Start Period**: `20s-60s` initial grace period

#### Dependency Management
```yaml
depends_on:
  postgres:
    condition: service_healthy
  cpp-engine:
    condition: service_healthy
```

## 5. Environment Configuration

### 5.1. Environment Variable Management

#### Core Configuration Variables
```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=simulated_trading_platform
DB_USER=trading_user
DB_PASSWORD=trading_password
POSTGRES_DB=simulated_trading_platform
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=trading_password
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/simulated_trading_platform

# API Configuration  
DOCKER_ENV=true
REACT_APP_API_URL=http://localhost:8000

# Development Options
CHOKIDAR_USEPOLLING=true  # File watching for hot reload
FAST_REFRESH=true         # React fast refresh
```

#### Environment File Structure
```
.env                      # Main environment configuration
docker-compose.yml        # Production configuration
docker-compose.dev.yml    # Development overrides
```

### 5.2. Configuration Management

#### Build-time Configuration
- **React Build Arguments**: API URL injection during build
- **Multi-stage Optimization**: Environment-specific builds
- **Dependency Installation**: Separate development/production deps

#### Runtime Configuration
- **Service Discovery**: Environment-based service URLs
- **Feature Flags**: Environment-controlled feature enablement
- **Resource Limits**: Container resource allocation

## 6. Deployment Procedures

### 6.1. Development Deployment

#### Quick Start Commands
```bash
# Start development environment
docker compose -f Docker/docker-compose.dev.yml up -d

# View service logs
docker compose -f Docker/docker-compose.dev.yml logs -f [service_name]

# Stop environment  
docker compose -f Docker/docker-compose.dev.yml down
```

#### Development Features
- **Hot Reload**: Automatic code updates without restart
- **Volume Mounts**: Live file system access
- **Debug Ports**: Database accessible on host port 5433
- **Log Access**: Real-time log streaming

### 6.2. Production Deployment

#### Production Commands
```bash
# Production deployment
docker compose -f Docker/docker-compose.yml up -d

# Health status check
docker compose -f Docker/docker-compose.yml ps

# Resource monitoring
docker stats
```

#### Production Optimizations
- **Multi-stage Builds**: Minimal runtime image sizes
- **Resource Limits**: Defined CPU/memory constraints
- **Security**: Minimal exposed ports and attack surface
- **Performance**: Optimized nginx and database configuration

### 6.3. Monitoring and Maintenance

#### Container Health Monitoring
```bash
# Service health status
docker compose ps

# Individual container health
docker inspect --format='{{.State.Health.Status}}' [container_name]

# Resource usage monitoring
docker stats --no-stream
```

#### Log Management
```bash
# Service-specific logs
docker compose logs [service_name]

# Follow logs in real-time
docker compose logs -f --tail=100

# Log rotation and cleanup
docker system prune -f
```

## 7. Troubleshooting and Operations

### 7.1. Common Issues and Solutions

#### Database Connection Issues
```bash
# Check database container health
docker inspect trading-db --format='{{.State.Health}}'

# Verify data population
docker exec trading-db psql -U trading_user -d simulated_trading_platform -c "SELECT COUNT(*) FROM stocks;"

# Reset database
docker volume rm postgres_data && docker compose up postgres -d
```

#### Engine Binary Issues
```bash
# Verify binary availability
docker exec trading-engine test -x /shared/trading_engine

# Check shared volume
docker volume inspect cpp_engine_shared

# Rebuild engine
docker compose build cpp-engine && docker compose up cpp-engine -d
```

#### API Service Issues
```bash
# Check API health endpoint
curl http://localhost:8000/health

# Verify environment variables
docker exec trading-api env | grep DATABASE_URL

# Review API logs
docker compose logs trading-api
```

### 7.2. Performance Optimization

#### Resource Optimization
- **Image Layers**: Multi-stage builds reduce image size
- **Dependency Caching**: Optimized Docker layer caching
- **Volume Performance**: Named volumes vs bind mounts
- **Network Optimization**: Minimal network hops

#### Scaling Considerations
- **Horizontal Scaling**: Multiple API container instances
- **Load Balancing**: Nginx upstream configuration
- **Database Scaling**: Read replicas for high load
- **Cache Layer**: Redis integration for session management

### 7.3. Security Best Practices

#### Container Security
- **Non-root Users**: Services run with minimal privileges
- **Network Isolation**: Services on dedicated networks
- **Secret Management**: Environment-based credential handling
- **Image Scanning**: Regular vulnerability assessment

#### Production Hardening
- **Port Restrictions**: Only necessary ports exposed
- **Resource Limits**: Prevent resource exhaustion attacks
- **Log Management**: Centralized logging with retention policies
- **Backup Strategy**: Automated database backups with point-in-time recovery