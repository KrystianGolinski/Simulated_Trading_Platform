# Simulated Trading Platform - Current Status Report

**Last Updated:** July 7, 2025  

## Version 1.3 

## Description:

**NEW**: Major simulation overhaul. Resolved survivorship bias (Still a few features need implementing for even more accurate metrics), the codebase is now **MUCH** cleaner and more maintainable than v1.2, platform is much more optimised, true parallelism has been achieved to **Massively Speed Up** simulation execution. The platform is really scalable right now. A lot of bad code was replaced with not so bad code.

---

Platform is correctly set up using 'setup.sh' featuring extensive testing ensuring:
- C++ engine is fully operational across all components
- API is fully operational and healthy across all endpoints
- Platform components are correctly interacting between each other

Platform is maintaining it's full docker containerisation, with containers sharing volumes and able to interact between each other.

The testing architecture is extensive, logging is setup for easy debugging, warnings displaying or generalised output. Errors are extensively created to determine causality easily. 

The user is correctly able to start a simulation from frontend with configurable parameters featuring multi-stock abilities (currently the platform has data for 44 symbols so that is the maximum but data limited not engine limited) and 2 strategies: MA_Crossover and RSI (Relative Strength Index). The strategies are successfully computed by the engine and the results are correctly displayed on the results screen. 

The platform now is starting to take shape, with clear future expansions planned.

## Simulation Execution Optimisations

The platform uses an intelligent, high-performance simulation execution system that automatically optimizes performance based on simulation complexity. The platform scales from simple single-stock backtests to complex multi-symbol parallel simulations ensuring optimal execution speeds for all simulations ready to expand the platform to more asset types and data points.

## Execution Flow

### 1. Intelligent Strategy Selection

When a simulation is submitted, the **Performance Optimizer** analyzes the request:

```
Simulation Request → Complexity Analysis → Strategy Selection → Execution
```

**Complexity Factors Analyzed:**
- Number of symbols (1-50 supported but data limited currently)
- Date range (days of historical data)
- Strategy computational complexity
- Available system resources

**Complexity Categories:**
- **Low** (< 5,000 complexity score): Simple sequential execution
- **Medium** (5,000 - 25,000): Optimized sequential with caching
- **High** (25,000 - 100,000): Parallel execution with 2-3 groups
- **Extreme** (> 100,000): Maximum parallelization with 4+ groups

### 2. Dynamic Execution Strategies

#### Sequential Execution (Simple Simulations)
```
Single Symbol or Low Complexity → C++ Engine → Results
```

- **Used for**: 1-5 symbols, short date ranges
- **Benefits**: Lower overhead, faster startup
- **Performance**: Optimized for simplicity

#### Parallel Execution (Complex Simulations)
```
Multi-Symbol Request → Symbol Grouping → Parallel C++ Engines → Result Aggregation
```

- **Used for**: 6+ symbols, long date ranges, complex strategies
- **Benefits**: 2-4x speedup for large simulations
- **Groups**: Symbols intelligently distributed across parallel workers

### 3. Symbol Grouping Algorithm

For parallel execution, symbols are distributed using **balanced grouping**:

```python
# Example: 44 symbols across 4 groups
Group 0: [AAPL, ABNB, ADBE, AMC, AMZN, BAC, BB, CRM, CVX, DIS, DOCU]     # 11 symbols
Group 1: [GE, GME, GOOGL, HD, IBM, IWM, JNJ, JPM, KO, LYFT, MA]          # 11 symbols  
Group 2: [META, MMM, MSFT, NFLX, NOK, NVDA, PG, PTON, QCOM, QQQ, SNOW]   # 11 symbols
Group 3: [SPY, T, TSLA, UBER, UNH, V, VTI, VXUS, WMT, X, XOM]            # 11 symbols
```

**Grouping Principles:**
- **Load balancing**: Equal symbols per group
- **Resource optimization**: Groups sized for available CPU cores
- **Memory efficiency**: Groups fit within memory constraints

### 4. C++ Engine Integration

Each execution (sequential or parallel group) uses the **high-performance C++ trading engine**:

#### Features:
- **Survivorship bias mitigation**: Dynamic temporal validation
- **Real-time progress reporting**: 50 day intervals via JSON on stderr
- **Memory efficiency**: Optimized data structures for large datasets
- **Strategy execution**: Pluggable trading algorithm framework

#### Progress Tracking:
```json
{"type": "progress", "progress_pct": 45.0, "current_date": "2023-06-15", "current_value": 12543.21}
```

### 5. Result Aggregation (Parallel Simulations)

When parallel groups complete, results are intelligently combined:

#### Aggregation Strategy:
- **Performance Metrics**: Use C++ engine calculated values from representative group
- **Trade Logs**: Combine and sort chronologically across all groups
- **Portfolio Values**: Aggregate daily balances accounting for all positions
- **Optimization Info**: Track parallel efficiency and speedup achieved

#### Example Aggregation:
```
Group 0 Result: 15.2% return, 23 trades → 
Group 1 Result: 18.7% return, 31 trades → Combined: 16.8% return, 89 trades
Group 2 Result: 12.4% return, 19 trades → 
Group 3 Result: 21.1% return, 16 trades → 
```

### 6. Real-Time Progress Updates

The platform provides **live progress tracking** for both execution modes:

#### Sequential Progress:
```
Frontend ← API ← ExecutionService ← C++ Engine (single instance)
```

#### Parallel Progress:
```
Frontend ← API ← Aggregated Progress ← Multiple ExecutionServices ← Multiple C++ Engines
```

**Aggregation Formula:**
```
Overall Progress = (Sum of all group progress) / Total groups
```

### 7. Performance Optimizations

#### Caching Strategy:
- **Stock data caching**: Frequently accessed historical data
- **Strategy result caching**: Reuse calculations for similar configurations  
- **Database connection pooling**: Efficient data access

#### Resource Management:
- **Worker thread limits**: Prevents system overload
- **Memory monitoring**: Automatic group sizing based on available RAM
- **CPU affinity**: Optimal core utilization for parallel groups

#### Estimation Engine:
```
Estimated Speedup = min(Number of Groups, Available CPU Cores) × Amdahl's Law Factor
Parallel Efficiency = Actual Speedup / Theoretical Maximum
```

### 8. Error Handling & Recovery

#### Robust Error Management:
- **Individual group failures**: Don't fail entire simulation
- **Timeout handling**: Prevent hanging simulations
- **Resource cleanup**: Automatic cleanup of failed processes
- **Detailed diagnostics**: Comprehensive error reporting

#### Failure Scenarios:
```
Single Group Fails → Continue with remaining groups → Partial results
All Groups Fail → Fall back to sequential execution → Full retry
```

### 9. Performance Monitoring

#### Metrics Tracked:
- **Execution time**: Sequential vs parallel performance
- **Resource utilization**: CPU, memory, I/O usage
- **Speedup achieved**: Actual vs estimated performance gains
- **Success rates**: Completion rates for different complexity levels

#### Performance Dashboard:
```json
{
  "parallel_executions": 127,
  "average_speedup": 2.8,
  "efficiency": 0.74,
  "resource_utilization": "68%"
}
```
## API

The API is efficient, standardised and adequately documented at `Project_Documentation/APIstructure.md`

## Engine

The engine succesfully powers the platform. Python FastAPI communicates with C++ engine via subprocess execution and JSON for data exchange. 

## Frontend

The frontend is not the strong point of the platform just yet

## Data

Daily data for 44 stocks for about 10 years, sufficient for testing. Needs scaling. Scaling infrastructure such as pagination is already in place, platform is scalable.

## Testing

Extensive testing structure throughout, adequate debug options, easy error tracing for causation, very solid foundation to begin development. Testing coverage covers all crucial aspects of the platform ensuring integrity is maintained. Error handling is structured and categorised in the API.

## Multi-platformity

Works on Linux. No Windows compatibility, not planned for anytime soon (bigger priorities).

## Scalability

Platform is scalable, the current codebase is clean, maintainable and scalable providing the perfect start for expansions. Strategies use a plugin structure, with dynamic strategy parameter loading enabling new strategies to be added easily. Pagination with TimescaleDB PostgreSQL allows for future data expansions into new asset types and broader asset quantities. Engine utilises multi-threading with thread-safety prioritsied with mutex's ensuring more intensive simulations still get completed in swift manner. Simulation execution runs complex intelligent algorithms to ensure optimal execution times.

## Planned Improvements (Code Side)

These improvements will generally not affect the overall usability of the platform to users or it's abilities but will improve code quality.

- (Quick Fix) Add symbol field to trade orders for accurate trade logs -> after that they can then be stored in DB etc
- Implement portfolio rebalancing for more accurate metrics
- Implement a dashboard to show real-time logging and exactly what   is happening at all times on the platform. See real time metrics of simulations not just at the results page. General admin dashboard. Long-term goal.
- Abstract base classes for engine services using interfaces
- Ensuring service configurations are centralized through dedicated service to implement configuration management
- Fix terrible frontend code

## Planned Major Expansions (User Side)

These may be featured in version 2.0 of the platform. Improving code quality takes priority over these features.

- Multiple asset type simulations (Stocks, minerals, crypto etc)
- Fully customisable asset configurations in simulations
- Cleaner frontend (more graphs, better layout, less jank)
- More strategy types
- More data
- Simulation saving, exporting...
- General platform improvements


--------Legal Notice---------
Krystian Golinski © 
This project is for personal and showcase purposes only.
Unauthorized use, reproduction, distribution, or modification is not permitted without explicit written consent.
Do not copy or submit any part of this work as your own.
