# System Architecture Technical Documentation

## 1. Introduction

This document provides a comprehensive technical overview of the Simulated Trading Platform's system architecture, covering the integration and interaction patterns between all platform components. It serves as the authoritative guide for understanding the complete system design and component relationships.

**Platform Version:** 1.3  
**Architecture Pattern:** Microservices with containerized deployment  
**Communication:** REST APIs with JSON message format  
**Data Flow:** Event-driven with real-time progress tracking  
**Deployment:** Docker Compose orchestration with service dependency management  

### 1.1. System Overview

The Simulated Trading Platform is a full-stack, containerized application designed for high-performance trading simulation and backtesting. The architecture emphasizes separation of concerns, scalability, and maintainability through service-oriented design.

**Core Capabilities:**
- **Historical Trading Simulation**: Execute trading strategies against historical stock data
- **Real-time Progress Monitoring**: Live simulation tracking with progress reporting
- **Performance Analytics**: Comprehensive trading performance metrics and risk analysis
- **Interactive Visualization**: Advanced charting and data exploration capabilities
- **Survivorship Bias Mitigation**: Temporal validation ensuring historically accurate backtests
- **Strategy Extensibility**: Plugin-based strategy architecture for custom trading algorithms

### 1.2. Architectural Principles

The system architecture adheres to modern software engineering principles:

- **Microservices Architecture**: Loosely coupled services with clear boundaries and responsibilities
- **Container-First Design**: Docker-native architecture with orchestrated service management
- **API-First Approach**: Well-defined REST interfaces for inter-service communication
- **Data Consistency**: Temporal accuracy and survivorship bias prevention across all operations
- **Performance Optimization**: High-performance C++ engine with efficient data processing
- **Scalability**: Service isolation enabling independent scaling and deployment
- **Observability**: Comprehensive logging, monitoring, and health checking across all components
- **Security**: Network isolation, credential management, and input validation

## 2. System Architecture Overview

### 2.1. Component Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│              Client Layer (Port 3000 dev / 80 prod)                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                React TypeScript Frontend                                    │ │
│  │  • Interactive Dashboard • Simulation Setup • Real-time Progress           │ │
│  │  • Results Visualization • Stock Chart Components • State Management       │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │ HTTP/REST API Calls (CORS Enabled)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          API Gateway Layer (Port 8000)                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        FastAPI Service                                     │ │
│  │                                                                             │ │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │ │
│  │ │Health Endpoints │ │Stock Data APIs  │ │Simulation APIs  │ │Strategy APIs│ │ │
│  │ │• /health/*      │ │• /stocks/*      │ │• /simulation/*  │ │• /strategies│ │ │
│  │ │• System Status  │ │• OHLCV Data     │ │• Lifecycle Mgmt │ │• Discovery  │ │ │
│  │ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘ │ │
│  │                                                                             │ │
│  │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │ │                  RouterBase Pattern Infrastructure                      │ │ │
│  │ │• Dependency Injection • Response Formatting • Error Handling           │ │ │
│  │ │• Correlation ID Tracking • Validation • Logging                        │ │ │
│  │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───┬───────────────────────────────────────────┘
                                  │   │
                    Database      │   │    C++ Engine Integration
                    Queries       │   │    (Shared Volume)
                                  ▼   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Data & Processing Layer                                 │
│                                                                                 │
│ ┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐ │
│ │        TimescaleDB Database         │ │        C++ Trading Engine          │ │
│ │           (Port 5432)               │ │         (Shared Binary)             │ │
│ │                                     │ │                                     │ │
│ │ ┌─────────────────────────────────┐ │ │ ┌─────────────────────────────────┐ │ │
│ │ │         Hypertable              │ │ │ │      Command Dispatcher        │ │ │
│ │ │   stock_prices_daily            │ │ │ │  • --simulate • --backtest      │ │ │
│ │ │   • OHLCV time-series data      │ │ │ │  • --test-db  • --status        │ │ │
│ │ │   • Monthly chunk intervals     │ │ │ └─────────────────────────────────┘ │ │
│ │ └─────────────────────────────────┘ │ │                                     │ │
│ │ ┌─────────────────────────────────┐ │ │ ┌─────────────────────────────────┐ │ │
│ │ │      Stock Metadata             │ │ │ │     Trading Orchestrator        │ │ │
│ │ │   • Symbol information          │ │ │ │  • Simulation lifecycle         │ │ │
│ │ │   • Temporal validation data    │ │ │ │  • Strategy execution           │ │ │
│ │ │   • IPO/delisting tracking      │ │ │ │  • Portfolio management         │ │ │
│ │ └─────────────────────────────────┘ │ │ └─────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────┐ │ │                                     │ │
│ │ │   Temporal Functions            │ │ │ ┌─────────────────────────────────┐ │ │
│ │ │   • is_stock_tradeable()        │ │ │ │    Performance Components       │ │ │
│ │ │   • get_eligible_stocks()       │ │ │ │  • Technical Indicators         │ │ │
│ │ │   • Survivorship bias prevention│ │ │ │  • Result Calculator            │ │ │
│ │ └─────────────────────────────────┘ │ │ │  • Progress Reporting          │ │ │
│ └─────────────────────────────────────┘ │ └─────────────────────────────────┘ │ │
└─────────────────────────────────────────┴─────────────────────────────────────┘
```

### 2.2. Service Integration Patterns

#### Request-Response Flow
1. **Client Request**: React frontend initiates API request with correlation ID
2. **API Gateway**: FastAPI validates request and routes to appropriate service
3. **Business Logic**: Service layer processes request using dependency injection
4. **Data Access**: Repository pattern accesses TimescaleDB via connection pools  
5. **Engine Coordination**: API orchestrates C++ engine execution via shared volume
6. **Response Assembly**: Standardized JSON response with metadata and correlation tracking
7. **Client Update**: Frontend updates state and UI based on response data

#### Real-time Communication
- **Polling Service**: Frontend polls simulation status endpoints for progress updates
- **Progress Streaming**: C++ engine outputs JSON progress to stderr for API consumption
- **State Synchronization**: Service layer maintains simulation state across requests
- **Error Propagation**: Comprehensive error handling with user-friendly messages

## 3. Component Integration

### 3.1. Frontend-API Integration

#### Communication Architecture
**Protocol**: HTTP/REST with JSON payloads  
**Authentication**: Correlation ID tracking for request tracing  
**Error Handling**: Standardized error response format with categorization  
**State Management**: Service layer with observer pattern for reactive updates  

#### API Integration Patterns
```typescript
// Service layer abstraction
export class SimulationService {
  async startSimulation(config: SimulationConfig): Promise<void> {
    const response = await simulationAPI.startSimulation(config);
    this.startStatusPolling(response.simulation_id);
  }
}

// Custom hooks integration
export const useSimulation = (): UseSimulationReturn => {
  const [state, setState] = useState(() => simulationService.getState());
  useEffect(() => simulationService.subscribe(setState), []);
}
```

#### Real-time Features
- **Progress Polling**: Configurable polling intervals with automatic backoff
- **Status Updates**: Live simulation progress with ETA calculations
- **Error Recovery**: Automatic retry mechanisms with user notification
- **State Persistence**: Simulation state maintained across page refreshes

### 3.2. API-Database Integration

#### Data Access Architecture
**Connection Management**: asyncpg connection pooling with health monitoring  
**Query Optimization**: Prepared statements with parameter binding  
**Transaction Support**: ACID compliance for complex operations  
**Caching Layer**: In-memory TTL cache for frequently accessed data  

#### Repository Pattern Implementation
```python
class StockDataRepository:
    def __init__(self, db_manager, cache_manager):
        self.db = db_manager
        self.cache = cache_manager
    
    async def get_stock_prices(self, symbol: str, start_date: date, end_date: date):
        cache_key = f"prices:{symbol}:{start_date}:{end_date}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query with prepared statement
        query = "SELECT * FROM stock_prices_daily WHERE symbol = $1 AND time >= $2 AND time <= $3"
        result = await self.db.fetch(query, symbol, start_date, end_date)
        await self.cache.set(cache_key, result, ttl=300)
        return result
```

#### Temporal Validation Integration
- **Survivorship Bias Prevention**: Dynamic IPO/delisting validation during queries
- **Historical Accuracy**: Database functions ensure temporal correctness
- **Data Integrity**: Comprehensive validation before simulation execution

### 3.3. API-Engine Integration

#### Inter-Process Communication
**Mechanism**: Shared volume binary execution with JSON I/O  
**Binary Deployment**: C++ engine deployed to shared volume by container  
**Parameter Passing**: JSON configuration via command-line arguments  
**Result Handling**: Structured JSON output parsing with error handling  

#### Engine Orchestration Pattern
```python
class SimulationEngine:
    async def execute_simulation(self, config: SimulationConfig):
        # Prepare configuration
        engine_config = self._prepare_config(config)
        
        # Execute engine with timeout
        process = await asyncio.create_subprocess_exec(
            '/shared/trading_engine', '--simulate', '--config', json.dumps(engine_config),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Parse results
        stdout, stderr = await process.communicate()
        return self._parse_results(stdout, stderr)
```

#### Progress Integration
- **Real-time Monitoring**: Engine progress updates via stderr JSON streams
- **Status Coordination**: API aggregates progress data for frontend consumption
- **Error Handling**: Engine errors propagated through standardized error codes

### 3.4. Database-Engine Integration

#### Direct Database Access
**Connection**: C++ engine uses libpq for direct PostgreSQL access  
**Environment Configuration**: Database credentials via environment variables  
**Query Execution**: Prepared statements for security and performance  
**Connection Management**: Single connection per engine execution  

#### Data Flow Optimization
- **Efficient Queries**: Optimized SQL with proper indexing utilization
- **Temporal Functions**: Database-side temporal validation for performance
- **Result Streaming**: Large result sets processed in chunks to manage memory

## 4. Data Flow Architecture

### 4.1. Simulation Execution Data Flow

#### Complete Simulation Lifecycle
1. **Configuration Input**: Frontend collects simulation parameters with validation
2. **API Validation**: Comprehensive parameter validation using Pydantic models
3. **Symbol Validation**: Database verification of stock symbols and date ranges
4. **Temporal Validation**: IPO/delisting checks for historical accuracy
5. **Engine Preparation**: Configuration transformation for C++ engine format
6. **Simulation Execution**: C++ engine processes historical data chronologically
7. **Progress Reporting**: Real-time updates via stderr JSON to API to frontend
8. **Result Calculation**: Performance metrics and trade analysis computation
9. **Data Persistence**: Results stored in database for historical analysis
10. **Response Assembly**: Comprehensive results package returned to frontend
11. **Visualization**: Interactive charts and analysis tools for result exploration

#### Data Transformation Pipeline
```
User Input → Pydantic Models → Database Validation → Engine Config → 
Simulation → Raw Results → Performance Metrics → JSON Response → UI Display
```

### 4.2. Real-time Progress Tracking

#### Progress Data Flow
1. **Engine Progress**: C++ engine outputs JSON progress to stderr at 5% intervals
2. **API Capture**: Python API captures stderr stream and parses progress JSON
3. **State Management**: Progress data stored in service layer state management
4. **Frontend Polling**: React frontend polls API status endpoint every 2 seconds
5. **UI Updates**: Progress bar and status information updated reactively

#### Progress Message Format
```json
{
  "type": "progress",
  "simulation_id": "uuid",
  "progress_pct": 45.2,
  "current_date": "2023-06-15",
  "estimated_remaining": "2m 34s",
  "status": "running"
}
```

### 4.3. Error Handling and Recovery

#### Multi-layered Error Handling
1. **Frontend Validation**: Client-side validation with immediate user feedback
2. **API Validation**: Server-side validation with detailed error categorization
3. **Database Errors**: Connection and query error handling with retry logic
4. **Engine Errors**: C++ engine error capture and categorization
5. **Network Errors**: Automatic retry with exponential backoff
6. **User Notification**: Clear error messages with suggested recovery actions

#### Error Propagation Chain
```
Engine Error → API Error Handler → Standardized Error Response → 
Frontend Error Handler → User Notification → Recovery Action
```

## 5. Scalability and Performance

### 5.1. Horizontal Scaling Architecture

#### Service Scaling Strategy
- **API Layer**: Multiple FastAPI instances with load balancer
- **Database**: Read replicas for query distribution
- **Engine**: Parallel simulation execution across multiple worker containers
- **Frontend**: CDN distribution with edge caching

#### Container Orchestration
```yaml
# Production scaling example
services:
  trading-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
      restart_policy:
        condition: on-failure
```

### 5.2. Performance Optimization

#### Database Performance
- **Indexing Strategy**: Comprehensive indexing for time-series and temporal queries
- **Connection Pooling**: Efficient connection reuse across API instances
- **Query Optimization**: Prepared statements and query plan caching
- **Data Partitioning**: TimescaleDB hypertables with monthly chunks

#### Application Performance
- **Caching**: Multi-level caching (database, API, frontend)
- **Asynchronous Processing**: Non-blocking I/O throughout the stack
- **Lazy Loading**: Frontend component lazy loading with code splitting
- **Resource Management**: Efficient memory management in C++ engine

#### Network Performance
- **HTTP/2**: Modern protocol support for multiplexed connections
- **Compression**: Response compression for large datasets
- **CDN Integration**: Static asset distribution via content delivery networks
- **Connection Pooling**: Persistent connections with keepalive

#### Parallel Execution Architecture
- **Multi-threaded Engine**: C++ trading engine supports parallel simulation execution
- **Worker Pool**: Configurable number of worker threads for concurrent simulations
- **Resource Isolation**: Each simulation runs in isolated execution context
- **Load Balancing**: Automatic work distribution across available CPU cores
- **Memory Optimization**: Shared memory pools for efficient resource utilization

#### Performance Monitoring
- **Execution Metrics**: Real-time performance tracking and reporting
- **Resource Monitoring**: CPU, memory, and I/O utilization tracking
- **Bottleneck Detection**: Automatic identification of performance constraints
- **Optimization Recommendations**: System-generated performance improvement suggestions

### 5.3. Monitoring and Observability

#### Health Monitoring
- **Service Health**: Multi-level health checks with dependency validation
- **Performance Metrics**: Response times, throughput, and error rates
- **Resource Monitoring**: CPU, memory, and disk utilization tracking
- **Business Metrics**: Simulation success rates and user engagement

#### Logging Architecture
```
Application Logs → Structured JSON → Centralized Logging → 
Analysis Tools → Alerting → Operational Response
```

## 6. Plugin Architecture

### 6.1. Strategy Plugin System

#### Plugin Discovery and Registration
- **Plugin Directory**: External strategies stored in `Backend/api/plugins/strategies/`
- **Automatic Discovery**: Dynamic scanning and registration at API startup
- **Interface Validation**: Verification of strategy interface compliance
- **Configuration Validation**: Schema validation for plugin parameter definitions

#### Plugin Lifecycle Management
- **Dynamic Loading**: Runtime module import with error handling and isolation
- **Version Management**: Plugin versioning with compatibility checking
- **Hot Reload**: Plugin updates without system restart (development mode)
- **Dependency Resolution**: Automatic handling of plugin dependencies

#### Plugin Integration Architecture
```
Strategy Registry ← Plugin Discovery ← File System Scanner
        ↓                    ↓              ↓
  Validation     ← Interface Check ← Module Import
        ↓                    ↓              ↓
API Endpoints   ← Registration  ← Error Handling
```

#### Plugin Security Model
- **Sandboxed Execution**: Plugin strategies run in isolated contexts
- **Resource Limits**: Memory and CPU constraints for plugin execution
- **API Restrictions**: Limited access to system resources and sensitive data
- **Input Validation**: Comprehensive validation of plugin inputs and outputs

## 7. Security Architecture

### 7.1. Network Security

#### Container Network Isolation
- **Dedicated Networks**: Services on isolated Docker networks
- **Port Restrictions**: Only necessary ports exposed to host
- **Service Communication**: Internal service-to-service communication
- **Firewall Rules**: Network-level access controls

#### API Security
- **Input Validation**: Comprehensive parameter validation and sanitization
- **SQL Injection Prevention**: Parameterized queries throughout
- **CORS Configuration**: Controlled cross-origin resource sharing with `http://localhost:3000`
- **Rate Limiting**: Request throttling to prevent abuse

### 7.2. Data Security

#### Credential Management
- **Environment Variables**: Externalized credential configuration
- **Container Secrets**: Secure credential distribution
- **Database Access**: Principle of least privilege for database users
- **Network Encryption**: TLS for external communications

#### Data Protection
- **Input Sanitization**: All user input validated and sanitized
- **Query Parameterization**: Prevention of SQL injection attacks
- **Access Logging**: Comprehensive audit trail for data access
- **Backup Security**: Encrypted backups with secure storage

## 8. Deployment and Operations

### 8.1. Environment Management

#### Development Environment
- **Frontend Port**: 3000 for React development server with hot reload
- **Hot Reload**: Live code updates without container restart
- **Debug Access**: Database port exposure for development tools
- **Log Streaming**: Real-time log access for debugging
- **Volume Mounts**: Live file system access for rapid iteration
- **CORS**: Configured for `http://localhost:3000` development server

#### Production Environment
- **Frontend Port**: 80 for Nginx static file serving
- **Optimized Images**: Multi-stage builds with minimal runtime images
- **Resource Limits**: Defined CPU and memory constraints
- **Health Monitoring**: Automated health checks with recovery
- **Security Hardening**: Minimal attack surface and privilege restrictions
- **CORS**: Production-ready cross-origin configuration

### 8.2. Operational Procedures

#### Deployment Pipeline
```
Code Commit → Automated Tests → Container Build → 
Image Registry → Deployment → Health Validation → Traffic Routing
```

#### Maintenance Operations
- **Rolling Updates**: Zero-downtime deployments with health validation
- **Database Migrations**: Schema updates with backup and rollback procedures
- **Performance Tuning**: Continuous optimization based on metrics
- **Disaster Recovery**: Backup and restore procedures with RTO/RPO targets

### 8.3. Troubleshooting Procedures

#### Diagnostic Workflow
1. **Health Check Analysis**: Validate all service health statuses
2. **Log Analysis**: Review service logs for error patterns
3. **Performance Monitoring**: Check resource utilization and bottlenecks
4. **Database Analysis**: Validate database connectivity and query performance
5. **Network Diagnostics**: Verify inter-service communication
6. **Recovery Actions**: Systematic recovery procedures based on issue type

#### Common Issue Resolution
- **Service Restart**: Automated restart with health validation
- **Database Recovery**: Connection pool refresh and query optimization
- **Engine Issues**: Binary redeployment and configuration validation
- **Frontend Problems**: Cache clearing and bundle redeployment

This comprehensive system architecture provides the foundation for understanding, maintaining, and extending the Simulated Trading Platform across all its integrated components.