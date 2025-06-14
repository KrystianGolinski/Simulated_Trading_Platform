# Docker Configuration for Trading Platform

This directory contains all Docker-related configuration files for the Simulated Trading Platform.

## Files

- `docker-compose.dev.yml` - Development environment configuration
- `docker-compose.yml` - Production environment configuration  
- `docker-setup.sh` - Automated setup script
- `.env.example` - Environment variables template

## Quick Start

### From Project Root
```bash
./setup.sh
```

### From Docker Directory
```bash
cd Docker
./docker-setup.sh
```

## Services

### Development Environment (`docker-compose.dev.yml`)

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | React TypeScript UI |
| fastapi | 8000 | Python API backend |
| postgres | 5432 | PostgreSQL + TimescaleDB |
| redis | 6379 | Caching layer |
| cpp-engine | - | C++ trading engine |

### Production Environment (`docker-compose.yml`)

Optimized for production deployment with:
- Multi-stage builds
- Environment variable security
- Restart policies
- Optimized resource usage

## Commands

### Development
```bash
# Start all services
docker compose -f Docker/docker-compose.dev.yml up -d

# Stop all services  
docker compose -f Docker/docker-compose.dev.yml down

# View logs
docker compose -f Docker/docker-compose.dev.yml logs -f [service]

# Rebuild specific service
docker compose -f Docker/docker-compose.dev.yml up --build [service]
```

### Production
```bash
# Start production environment
docker compose -f Docker/docker-compose.yml up -d

# Stop production environment
docker compose -f Docker/docker-compose.yml down
```

## Environment Variables

Copy `.env.example` to `.env` in the project root and configure:

```bash
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://trader:password@postgres:5432/trading_platform
REDIS_URL=redis://redis:6379
NODE_ENV=development
```

## Network Configuration

All services run on a custom bridge network `trading_network` for internal communication while exposing necessary ports to the host.

## Volume Management

- `postgres_data` - PostgreSQL database persistence
- `redis_data` - Redis cache persistence
- Development mounts source code for hot reload

## Troubleshooting

### Permission Issues
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Conflicts
Check if ports are in use:
```bash
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
```

### Container Debugging
```bash
# Access container shell
docker compose -f Docker/docker-compose.dev.yml exec [service] /bin/bash

# Check container logs
docker compose -f Docker/docker-compose.dev.yml logs [service]
```