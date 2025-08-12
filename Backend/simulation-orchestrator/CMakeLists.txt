cmake_minimum_required(VERSION 3.16)
project(simulation-orchestrator)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add cpp-common as subdirectory
add_subdirectory(../cpp-common cpp-common-build)

# Create executable
add_executable(simulation-orchestrator
    src/main.cpp
    src/worker_spawner.cpp
    src/strategy_analyzer.cpp
    src/execution_planner.cpp
)

# Set include directories
target_include_directories(simulation-orchestrator PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../cpp-common/include
)

# Link libraries
target_link_libraries(simulation-orchestrator
    cpp-common
)

# Install rules
install(TARGETS simulation-orchestrator
    RUNTIME DESTINATION bin
)