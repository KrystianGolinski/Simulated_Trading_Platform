
# Engine Fix Plan - Simulation Issues Debug & Resolution

## Problem Analysis

### Current Issue
The trading simulation shows these critical problems:
1. **Instant completion**: Progress screen flashes for one frame then jumps to results
2. **Static results**: Always shows final value of $10,025.45 regardless of input capital
3. **No progress tracking**: Simulation appears to complete instantly
4. **Inconsistent capital**: Starting capital not being properly passed to C++ engine

### Root Cause Investigation

Based on code analysis, I've identified several interconnected issues:

#### 1. **C++ Engine Issues**
- **Hardcoded results**: The C++ engine is returning static/hardcoded values instead of actual simulation results
- **Capital parameter not used**: `runSimulationWithParams()` method exists but may not be using the capital parameter correctly
- **Date range ignored**: Engine may be using default date ranges instead of provided parameters
- **Strategy not executing**: Moving average crossover strategy may not be generating actual trades

#### 2. **FastAPI Integration Issues**
- **No progress feedback**: C++ subprocess runs synchronously without progress updates
- **Parameter passing**: Command-line arguments to C++ engine may not be correctly formatted
- **Result parsing**: JSON parsing happens after C++ process completes, no streaming

#### 3. **Frontend Flow Issues**
- **Polling too fast**: 2-second polling interval might be too fast for very quick simulations
- **Progress estimation**: Backend uses rough time-based estimation instead of actual progress
- **State transitions**: Simulation moves from 'pending' → 'running' → 'completed' too quickly

## Detailed Investigation Results

### C++ Engine Analysis (`main.cpp:line_189`)
The C++ engine responds to `--simulate` flag and calls `runSimulationWithParams()`, but the output shows:
- End date is hardcoded to "2023-12-31" (ignoring input "2023-01-31")
- Ending value is always 10,025.45
- Equity curve shows constant 10,000 values (no trading activity)

### Backend Analysis (`simulation_engine.py:line_122`)
The Python simulation engine:
- Correctly builds command-line arguments
- Calls C++ subprocess properly
- Logs commands for debugging (using `logger.error()`)
- Parses JSON results but doesn't validate content

### Frontend Analysis (`useSimulation.ts:line_78`)
The React hook:
- Polls every 2 seconds for status updates
- Expects progress updates that never come
- Immediately jumps to completed state

## Fix Strategy

### Phase 1: C++ Engine Core Fixes (High Priority)

#### 1.1 Fix Parameter Handling
**File:** `Backend/cpp-engine/src/main.cpp`
**Issues:**
- Argument parsing may not work correctly for all parameter formats
- Capital parameter not being passed through to backtest configuration
- Date ranges not being applied correctly

**Actions:**
- Debug argument parsing by adding logging output
- Verify `BacktestConfig` receives correct parameters
- Ensure `Portfolio` is initialized with correct capital

#### 1.2 Fix Trading Strategy Execution
**File:** `Backend/cpp-engine/src/trading_engine.cpp`
**Issues:**
- Strategy may not be executing trades
- Moving average calculations may be incorrect
- No actual buy/sell signals being generated

**Actions:**
- Add debug logging to strategy execution
- Verify moving average calculations
- Ensure trades are actually executed and recorded

#### 1.3 Fix Result Generation
**File:** `Backend/cpp-engine/src/trading_engine.cpp`
**Issues:**
- Results appear to be hardcoded or using default values
- Equity curve shows no trading activity
- Performance metrics not calculated from actual trades

**Actions:**
- Verify `BacktestResult` is populated with actual simulation data
- Fix equity curve generation to reflect actual portfolio values
- Calculate performance metrics from real trade data

### Phase 2: Progress Tracking Implementation (Medium Priority)

#### 2.1 C++ Progress Output
**Implementation Strategy:**
- Add progress output to C++ engine during simulation
- Output progress as separate JSON lines to stderr
- Include current date, percentage complete, and portfolio value

**Changes needed:**
- Modify backtest loop to output progress every N days
- Add `--progress` flag to enable progress output
- Use stderr for progress, stdout for final results

#### 2.2 Backend Progress Monitoring
**File:** `Backend/api/simulation_engine.py`
**Changes:**
- Monitor both stdout and stderr streams
- Parse progress updates from stderr
- Update simulation status in real-time
- Store progress information for frontend polling

#### 2.3 Frontend Progress Display
**File:** `Frontend/trading-platform-ui/src/hooks/useSimulation.ts`
**Changes:**
- Display actual progress percentages instead of estimates
- Show current simulation date
- Update progress bar with real data

### Phase 3: Parameter Validation & Error Handling (Medium Priority)

#### 3.1 Input Validation
**Backend validation:**
- Verify stock symbols exist in database
- Validate date ranges have available data
- Check capital amount is reasonable
- Validate strategy parameters

#### 3.2 Error Messaging
**Comprehensive error handling:**
- Database connection failures
- Invalid stock symbols
- Insufficient data for date range
- C++ engine compilation/execution errors

### Phase 4: Performance & Optimization (Low Priority)

#### 4.1 Simulation Speed
- Optimize database queries
- Improve memory management
- Add parallel processing for multi-symbol portfolios

#### 4.2 Caching
- Cache frequently accessed stock data
- Cache calculated technical indicators
- Store simulation results for replay


After implementing all fixes, verify these criteria:

**Core Functionality:**
- [ ] Different capital amounts produce proportionally different results
- [ ] Different date ranges affect the simulation duration and results
- [ ] Different symbols produce different trading patterns
- [ ] Moving average strategy generates actual buy/sell signals
- [ ] Equity curve shows realistic portfolio value changes over time

**Progress Tracking:**
- [ ] Progress updates from 0% to 100% during simulation
- [ ] Frontend progress bar updates in real-time
- [ ] Simulation doesn't appear to complete instantly
- [ ] Progress includes current date and portfolio value

**Integration:**
- [ ] Frontend → FastAPI → C++ engine parameter passing works
- [ ] Results are properly returned to frontend
- [ ] Error handling works for invalid inputs
- [ ] Multiple simulations can run concurrently

**Performance:**
- [ ] 1-month simulation completes in reasonable time (< 30 seconds)
- [ ] Memory usage remains stable during simulation
- [ ] No memory leaks or crashes

**Data Accuracy:**
- [ ] Starting capital correctly initializes portfolio
- [ ] Historical price data is properly loaded from database
- [ ] Trade calculations are mathematically correct
- [ ] Performance metrics match manual calculations

## Testing Strategy

### Unit Tests
- C++ engine with known input/output pairs
- Parameter parsing validation
- Trading strategy logic verification
- Performance metrics calculations

### Integration Tests
- FastAPI to C++ engine communication
- Database connectivity and data retrieval
- End-to-end simulation flow

### Manual Testing Scenarios
1. **Basic functionality**: AAPL, 2023-01-01 to 2023-01-31, $10,000
2. **Different capital**: Same dates, $5,000 vs $20,000
3. **Different timeframes**: 1 week, 1 month, 1 year
4. **Different symbols**: Test with MSFT, GOOGL, TSLA
5. **Strategy parameters**: Different MA periods (10/30, 50/200)

## Success Criteria

### Must Have (Phase 1)
- [ ] Simulation results vary with different input parameters
- [ ] Starting capital correctly affects position sizes and final results
- [ ] Date ranges are properly applied
- [ ] Basic trading strategy executes trades

### Should Have (Phase 2)
- [ ] Progress updates show actual simulation progress
- [ ] Frontend displays meaningful progress information
- [ ] Simulations complete in reasonable time with progress feedback

### Nice to Have (Phase 3)
- [ ] Comprehensive error handling and user feedback
- [ ] Input validation prevents invalid simulations
- [ ] Performance optimizations for larger simulations

## Risk Mitigation

### Technical Risks
1. **Database connectivity**: Ensure robust connection handling
2. **Memory usage**: Monitor for memory leaks in long simulations
3. **Process management**: Handle C++ subprocess failures gracefully

### Timeline Risks
1. **Complex C++ debugging**: Allocate extra time for low-level debugging
2. **Integration complexity**: Test each component independently first
3. **Performance issues**: Start with simple cases, optimize later

## Monitoring & Debugging Tools

### Development Tools
- Add debug flags to C++ engine for verbose output
- Use logging at all levels (C++, Python, React)
- Implement test endpoints for direct C++ engine testing

### Production Monitoring
- Log all simulation requests and results
- Monitor simulation completion times
- Track error rates and types
