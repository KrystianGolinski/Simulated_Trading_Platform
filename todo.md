# Architecture Issues & Refactoring Plan

The API layer is handling business operations which should be delegated and handled by the backend. The intended architecture for this project is that the API is simply a pass-through layer with backend handling all logic and routing. The following plan has been devised to refactor the current approach to better meet that approach.
The API layer contains **1,300+ lines of complex trading business logic** that belong in the C++ engine, making the API far more than a simple pass-through layer.

## Solution: Two executables architecture

Instead of adding business logic to the existing `trading_engine`, i'll create **two distinct C++ executables**:

1. **`trading_engine`** (The Worker) - Unchanged, pure trading logic for single symbol groups
2. **`simulation_orchestrator`** (The Manager) - New executable containing all business logic

**Key Benefits:**
- **API becomes ultra-simple** - single call to orchestrator handles everything
- **True separation of concerns** at every architectural level
- **Core trading logic stays pure** - no risk of breaking existing functionality
- **Enhanced testability** - test orchestration and trading logic independently

## Primary issue: `performance_optimizer.py` (1,299 lines)

This file contains extensive trading business logic that must move to the C++ orchestrator:
- Strategy complexity analysis and execution planning
- Mathematical performance modeling using Amdahl's Law  
- Symbol grouping algorithms and load balancing
- Parallel execution coordination across multiple processes
- Memory management decisions and optimization recommendations

---

## Implementation

### File Structure & Docker Deployment
**File Structure:** Clean separation with shared common library
**Docker Deployment:** Two containers (API + Backend)

```
./Backend/
├── api/ (Python - existing)
│   └── Dockerfile (builds API container)
├── trading-engine/ (renamed from cpp-engine)
│   ├── src/ (existing worker code)
│   ├── include/
│   ├── tests/
│   └── CMakeLists.txt
├── simulation-orchestrator/ (new manager)
│   ├── src/
│   ├── include/
│   └── CMakeLists.txt
├── cpp-common/ (shared library)
│   ├── include/ (SimulationConfig, WorkerResult, etc...)
│   ├── src/ (shared utilities)
│   └── CMakeLists.txt
└── Dockerfile (builds C++ backend container with 2 executables + shared library)
```

### Target Architecture (Two-Executable Approach)
```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Python)                      │
│                  ┌─────────────────────────────────┐        │
│                  │    Pure Pass-Through Layer      │        │
│                  │  • Request validation           │        │
│                  │  • Parameter transformation     │        │
│                  │  • Response formatting          │        │
│                  └─────────────────────────────────┘        │
└─────────────────────────────────┬───────────────────────────┘
                                  │ Single Call
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│              simulation-orchestrator (C++)                  │
│                        (The Manager)                        │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Strategy        │ │ Execution       │ │ Performance     │ │
│ │ Analysis        │ │ Planning        │ │ Optimization    │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Symbol          │ │ Parallel        │ │ Results         │ │
│ │ Grouping        │ │ Coordination    │ │ Aggregation     │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────┬───────────────────────────┘
                                  │ Spawns Workers
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                trading-engine (C++)                         │
│                    (The Worker)                             │
│                                                             │
│              ┌─────────────────────────────────┐            │
│              │     Core Trading Logic          │            │
│              │   • Single symbol group         │            │
│              │   • Atomic simulation           │            │
│              │   • Pure execution              │            │
│              └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- **API**: Single call to orchestrator, no business logic
- **Orchestrator**: Handles all complexity, parallelism, optimization
- **Worker**: Pure, focused trading engine - unchanged from current

## Implementation Plan

### Step 1: Restructure Directories
**Goal**: Rename and organize directories without breaking existing functionality

**Tasks:**
1. **Rename cpp-engine to trading-engine**
2. **Create simulation-orchestrator and cpp-common directories**
3. **Update Docker build structure**
4. **Test existing functionality still works**

### Step 2: Build Shared Library & IPC Protocol
**Goal**: Create cpp-common shared library and define orchestrator-worker communication

**Tasks:**
1. **Create Shared Data Structures (cpp-common)**
   ```cpp
   // cpp-common/include/simulation_config.hpp
   struct SimulationConfig {
       std::vector<std::string> symbols;
       std::string start_date;
       std::string end_date;
       double starting_capital;
       std::string strategy;
       nlohmann::json strategy_parameters;
       
       // Serialization methods
       std::string toJson() const;
       static SimulationConfig fromJson(const std::string& json);
   };
   
   // cpp-common/include/worker_result.hpp
   struct WorkerResult {
       std::vector<std::string> symbols;
       int return_code;
       std::string stdout_data;
       std::string stderr_data;
       nlohmann::json result_data;
       double execution_time_ms;
   };
   ```

2. **Define IPC Protocol**
   ```cpp
   // Orchestrator → Worker Communication:
   // 1. Pass config via command line: ./trading_engine --config-json '{"symbols":["AAPL"],...}'
   // 2. Worker writes results to stdout as JSON
   // 3. Worker returns 0 for success, non-zero for failure
   // 4. Worker writes errors to stderr for logging
   
   // simulation-orchestrator/src/worker_spawner.cpp
   class WorkerSpawner {
       WorkerResult spawnWorker(const SimulationConfig& config);
       std::vector<WorkerResult> spawnParallelWorkers(const std::vector<SimulationConfig>& configs);
   };
   ```

3. **Create Basic Orchestrator Structure**

### Step 3: Implement Business Logic Classes
**Goal**: Migrate performance_optimizer.py logic to C++ with configuration transformation

**Tasks:**
1. **Implement Core Business Logic Classes** (Migrated from performance_optimizer.py)
2. **Design Configuration Transformation Logic**
3. **Create CMakeLists.txt with cpp-common dependency**

### Step 4: API Integration
**Goal**: Connect API to use simulation-orchestrator instead of performance_optimizer.py

**Tasks:**
1. **Update execution_service.py**
2. **Simplify simulation_engine.py**
3. **Remove performance_optimizer.py dependencies**

### Step 4: Testing & Validation
**Goal**: Ensure functionality parity and performance

**Tasks:**
1. **Integration Testing**
2. **Performance Testing**
3. **API Compatibility Testing**

### Step 5: Final Cleanup
**Goal**: Remove obsolete Python business logic and finalize architecture

**Tasks:**
1. **Delete performance_optimizer.py**
2. **Clean up API imports and dependencies**
3. **Documentation and Deployment Updates**

## Files affected

### Files to DELETE:
- `Backend/api/performance_optimizer.py` (1,299 lines of misplaced logic moved to C++)

### Files to HEAVILY MODIFY:
- `Backend/api/simulation_engine.py` (remove orchestration logic, simplify to single call)
- `Backend/api/services/execution_service.py` (add orchestrator call method)

### Files to CREATE:
- `Backend/cpp-common/` (shared library)
  - `include/simulation_config.hpp` (shared data structures)
  - `include/worker_result.hpp` (shared result structures)
  - `src/` (shared utility implementations)
  - `CMakeLists.txt` (shared library build)
- `Backend/simulation-orchestrator/` (new directory)
  - `src/main.cpp` (orchestrator entry point)
  - `src/strategy_analyzer.cpp` (from performance_optimizer.py logic)
  - `src/execution_planner.cpp` (from performance_optimizer.py logic)
  - `src/parallel_coordinator.cpp` (from performance_optimizer.py logic)
  - `src/config_transformer.cpp` (configuration breakdown logic)
  - `src/worker_spawner.cpp` (IPC communication with workers)
  - `include/` (header files)
  - `CMakeLists.txt` (orchestrator build configuration)

### Files to RENAME:
- `Backend/cpp-engine/` → `Backend/trading-engine/`

### Files to MODIFY:
- `Backend/Dockerfile` (build both executables in single container)
- `Backend/api/simulation_engine.py` (remove business logic, add orchestrator call)
- `Backend/api/services/execution_service.py` (add orchestrator execution method)

### Files UNCHANGED:
- `Backend/trading-engine/src/` (existing worker code stays pure)
- `Backend/api/routers/` (endpoints work the same)
- All current trading logic in worker remains untouched

## Benefits

- Moving logic to C++ will **significantly improve** performance
- Reduced API layer complexity will **reduce** latency
- Better resource utilization with native C++ execution

## Requirements

- C++ development for orchestrator implementation
- Maintain API compatibility during migration
- Comprehensive testing of orchestrator ↔ worker communication

---

### Why the two-Executable approach:

1. **API Layer Becomes Ultra-Simple**: Just one call to `simulation_orchestrator`
2. **Core Trading Logic Stays Pure**: `trading_engine` unchanged and focused
3. **Perfect Separation of Concerns**: Manager vs Worker responsibilities clearly defined
4. **Easy Testing**: Test orchestration logic and trading logic independently
5. **Future-Proof**: Could easily distribute workers across multiple machines