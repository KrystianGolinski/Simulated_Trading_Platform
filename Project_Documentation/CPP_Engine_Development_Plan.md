# C++ Simulation Engine Development Plan

## Overview
This document provides a comprehensive step-by-step plan to build the C++ simulation engine from scratch, integrate it with the existing FastAPI backend, and test throughout development.

## Current State Assessment
- ✅ Frontend: Complete with mock data integration
- ✅ Database: TimescaleDB with historical data loaded
- ✅ FastAPI: Basic endpoints working (`/health`, `/stocks`, `/stocks/{symbol}/data`)
- ❌ C++ Engine: Only placeholder `main.cpp`
- ❌ Simulation Logic: No trading algorithms implemented
- ❌ Integration: Missing simulation endpoints in FastAPI

## Development Strategy: Incremental Build & Test

### Philosophy
Build the engine in small, testable increments. Each phase should produce a working system that can be tested end-to-end with the frontend.

---

## Phase 1: Core Data Structures

### Goal
Create fundamental classes that can hold and manipulate trading data.

### 1.1 Project Structure Setup
**File: `Backend/cpp-engine/CMakeLists.txt`**
```cmake
# Update to include multiple source files and libraries
```

**Create directory structure:**
```
Backend/cpp-engine/
├── include/
│   ├── portfolio.h
│   ├── position.h
│   ├── order.h
│   ├── market_data.h
│   └── trading_engine.h
├── src/
│   ├── portfolio.cpp
│   ├── position.cpp
│   ├── order.cpp
│   ├── market_data.cpp
│   ├── trading_engine.cpp
│   └── main.cpp
├── tests/
│   └── test_basic.cpp
└── build/
```

### 1.2 Basic Classes Implementation

**Priority Order:**
1. **Position** - Track individual stock holdings
2. **Portfolio** - Manage collection of positions + cash
3. **Order** - Buy/sell instructions
4. **MarketData** - Price data access
5. **TradingEngine** - Main simulation controller

### 1.3 Testing Strategy Phase 1
**Create simple unit tests:**
- Position: Can buy/sell shares, calculate value
- Portfolio: Can add positions, track total value
- Order: Can create buy/sell orders with validation

**Test Command:**
```bash
cd Backend/cpp-engine/build
cmake .. && make && ./test_basic
```

### 1.4 Integration Test Phase 1
**Goal:** Return hardcoded portfolio value to frontend

**Steps:**
1. Compile C++ to executable that prints JSON
2. Modify FastAPI to call C++ executable
3. Test with frontend mock data

---

## Phase 2: Database Integration

### Goal
Connect C++ engine to PostgreSQL to read historical stock data.

### 2.1 Database Connection
**Add to CMakeLists.txt:**
- PostgreSQL client library (libpq)
- JSON library (nlohmann/json)

**Implement:**
- Database connection class
- SQL query execution
- Error handling

### 2.2 Market Data Access
**Features:**
- Read stock prices for specific date ranges
- Handle missing data gracefully
- Cache frequently accessed data

### 2.3 Testing Strategy Phase 2
**Unit Tests:**
- Database connection and disconnection
- Query execution with sample data
- Date range filtering

**Integration Test:**
```bash
# Test database connectivity
./trading_engine --test-db --symbol=AAPL --start=2023-01-01 --end=2023-12-31
```

### 2.4 Frontend Integration Test
**Goal:** Display real stock data from C++ engine

**Expected Output:** JSON with actual historical prices
```json
{
  "symbol": "AAPL",
  "data_points": 252,
  "date_range": ["2023-01-01", "2023-12-31"],
  "status": "success"
}
```

---

## Phase 3: Basic Trading Logic

### Goal
Implement moving average crossover strategy that can execute trades.

### 3.1 Technical Indicators
**Implement:**
- Simple Moving Average calculation
- Moving Average crossover detection
- Signal generation (buy/sell/hold)

### 3.2 Trading Strategy
**Create base strategy interface:**
```cpp
class TradingStrategy {
public:
    virtual Signal evaluateSignal(const MarketData& data, const Portfolio& portfolio) = 0;
    virtual void configure(const StrategyConfig& config) = 0;
};
```

**Implement MA Crossover:**
- Configurable short/long periods (20/50 days default)
- Position sizing logic
- Risk management basics

### 3.3 Testing Strategy Phase 3
**Unit Tests:**
- Moving average calculations accuracy
- Signal generation logic
- Edge cases (insufficient data, flat markets)

**Backtesting Test:**
```bash
# Run 1-month test with known data
./trading_engine --backtest --symbol=AAPL --start=2023-01-01 --end=2023-02-01 --capital=10000
```

**Expected Output:**
```json
{
  "starting_capital": 10000,
  "ending_value": 10250,
  "return_pct": 2.5,
  "trades": 3,
  "signals_generated": 5
}
```

---

## Phase 4: Full Simulation Engine

### Goal
Complete simulation engine that processes multiple stocks over extended periods.

### 4.1 Multi-Stock Support
**Features:**
- Portfolio diversification across multiple symbols
- Position sizing per stock
- Rebalancing logic

### 4.2 Time-Series Processing
**Implement:**
- Day-by-day simulation loop
- Event-driven architecture
- Order execution timing

### 4.3 Performance Metrics
**Calculate:**
- Total return percentage
- Sharpe ratio (if time permits)
- Maximum drawdown
- Win/loss ratio
- Equity curve generation

### 4.4 Testing Strategy Phase 4
**Performance Tests:**
```bash
# Test with realistic portfolio
./trading_engine --backtest \
  --symbols=AAPL,MSFT,GOOGL,AMZN,TSLA \
  --start=2022-01-01 --end=2023-12-31 \
  --capital=100000 \
  --output=results.json
```

**Validation:**
- Results should be reproducible
- Equity curve should be realistic
- Performance metrics should calculate correctly

---

## Phase 5: FastAPI Integration

### Goal
Create seamless integration between C++ engine and FastAPI backend.

### 5.1 Process Communication
**Implementation Options:**
1. **Subprocess calls** (Recommended for MVP)
2. Python C++ bindings (pybind11)
3. REST API between services

**Chosen: Subprocess Approach**
- Fastest to implement
- Easy to debug
- Clear separation of concerns

### 5.2 New FastAPI Endpoints

**Add to `Backend/api/main.py`:**

```python
@app.post("/simulation/start")
async def start_simulation(config: SimulationConfig):
    # Launch C++ engine with parameters
    # Return simulation_id
    
@app.get("/simulation/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    # Check if C++ process is running
    # Return progress information
    
@app.get("/simulation/{simulation_id}/results")
async def get_simulation_results(simulation_id: str):
    # Read results JSON from C++ engine
    # Return formatted results
```

### 5.3 Configuration Management
**Create:**
- JSON configuration schema
- Parameter validation
- Default value handling

### 5.4 Testing Strategy Phase 5
**API Tests:**
```bash
# Test simulation start
curl -X POST "http://localhost:8000/simulation/start" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "starting_capital": 10000,
    "strategy": "ma_crossover",
    "short_ma": 20,
    "long_ma": 50
  }'

# Test results retrieval
curl "http://localhost:8000/simulation/123/results"
```

---

## Phase 6: End-to-End Integration

### Goal
Complete working system from frontend to C++ engine and back.

### 6.1 Frontend API Calls
**Update React components:**
- Remove mock data from `App.tsx`
- Connect `SimulationSetup` to `POST /simulation/start`
- Implement polling for simulation status
- Display real results in `SimulationResults`

### 6.2 Error Handling
**Comprehensive error management:**
- C++ exceptions and error codes
- FastAPI error responses
- Frontend error display
- Graceful failure modes

### 6.3 Performance Optimization
**Target Performance:**
- 1-year backtest on 5 stocks: < 10 seconds
- Memory usage: < 500MB
- CPU usage: Efficient single-threaded

### 6.4 Testing Strategy Phase 6
**Full System Tests:**

1. **Quick Test (5 minutes):**
   ```bash
   # Frontend → API → C++ → Results
   # Start simulation through UI
   # Verify results display correctly
   ```

2. **Stress Test (30 minutes):**
   ```bash
   # Multiple concurrent simulations
   # Large date ranges (5+ years)
   # Many stocks (10+)
   ```

3. **Edge Case Testing:**
   - Invalid date ranges
   - Non-existent stocks
   - Network failures
   - Database unavailable

---

## Testing Throughout Development

### Continuous Integration Approach

**Daily Testing Routine:**
1. **Unit Tests:** Run after each code change
2. **Integration Tests:** Run before committing
3. **Performance Tests:** Run weekly
4. **End-to-End Tests:** Run before major releases

### Test Data Management
**Create standardized test datasets:**
- Small dataset: 1 stock, 1 month (for quick tests)
- Medium dataset: 3 stocks, 6 months (for integration)
- Large dataset: 10 stocks, 2 years (for performance)

### Debugging Strategies
**Logging Implementation:**
- C++: stdout/stderr with timestamps
- FastAPI: structured logging to files
- Frontend: console.log with debug levels

**Common Issues to Watch:**
- Memory leaks in C++ (use valgrind)
- Database connection timeouts
- JSON parsing errors
- Date/timezone handling

---

## Development Environment Setup

### Required Tools
```bash
# C++ Development
sudo apt-get install build-essential cmake
sudo apt-get install libpq-dev  # PostgreSQL client
sudo apt-get install nlohmann-json3-dev  # JSON parsing

# Testing Tools
sudo apt-get install valgrind  # Memory debugging
sudo apt-get install gtest  # Unit testing (optional)

# Python Dependencies (already installed)
# FastAPI, asyncpg, uvicorn
```

### Build Scripts
**Create `Backend/cpp-engine/build.sh`:**
```bash
#!/bin/bash
cd "$(dirname "$0")"
mkdir -p build
cd build
cmake ..
make -j$(nproc)
echo "Build complete. Run ./trading_engine --help for usage."
```

### Development Workflow
**Daily Development Cycle:**
1. Write/modify C++ code
2. Run unit tests: `./test_basic`
3. Build: `./build.sh`
4. Test integration: Start FastAPI and test endpoints
5. Test frontend: Verify UI still works
6. Commit changes

---

## Success Metrics

### Phase Completion Criteria

**Phase 1:** ✅ Basic classes compile and pass unit tests

**Phase 2:** ✅ Can read stock data from database

**Phase 3:** ✅ Can generate buy/sell signals

**Phase 4:** ✅ Can run complete backtest

**Phase 5:** ✅ FastAPI can call C++ engine

**Phase 6:** ✅ Frontend displays real simulation results

### Final Success Criteria
- [ ] 1-year backtest on 5 stocks completes in < 10 seconds
- [ ] Results are reproducible (same inputs = same outputs)
- [ ] No memory leaks or crashes during normal operation
- [ ] Frontend can start simulation and display results
- [ ] Error handling works for all failure modes

### Performance Benchmarks
**Target Metrics:**
- Startup time: < 2 seconds
- Data loading: < 5 seconds for 1 year of data
- Simulation execution: < 1 second per year per stock
- Memory usage: < 100MB base + 1MB per stock-year

---

## Risk Management & Contingencies

### Technical Risks
1. **C++ Complexity:** Start simple, add features incrementally
2. **Database Performance:** Optimize queries, add indexing
3. **Integration Complexity:** Use subprocess for MVP, optimize later
4. **Memory Management:** Use smart pointers, regular valgrind checks

## Next Steps

### Immediate Actions
1. Set up C++ project structure and build system
2. Implement basic Position and Portfolio classes
3. Create unit tests and verify compilation

### Phase 1 Deliverable
- C++ classes compile successfully
- Basic unit tests pass
- Can create portfolio and add positions
- Integration test: C++ outputs JSON that frontend can parse
