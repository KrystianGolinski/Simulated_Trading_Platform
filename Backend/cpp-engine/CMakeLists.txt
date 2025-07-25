cmake_minimum_required(VERSION 3.16)
project(TradingEngine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -pedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# Threading support
find_package(Threads REQUIRED)

# Source files for main executable
set(CORE_SOURCES
    src/position.cpp
    src/portfolio.cpp
    src/order.cpp
    src/market_data.cpp
    src/trading_engine.cpp
    src/result_calculator.cpp
    src/data_processor.cpp
    src/strategy_manager.cpp
    src/trading_orchestrator.cpp
    src/database_connection.cpp
    src/technical_indicators.cpp
    src/trading_strategy.cpp
    src/portfolio_allocator.cpp
    src/argument_parser.cpp
    src/command_dispatcher.cpp
    src/data_conversion.cpp
    src/json_helpers.cpp
    src/logger.cpp
    src/execution_service.cpp
    src/progress_service.cpp
    src/result.cpp
    src/error_utils.cpp
    src/date_time_utils.cpp
)


# Main executable
add_executable(trading_engine src/main.cpp ${CORE_SOURCES})

# Test executable
add_executable(test_comprehensive tests/test_comprehensive.cpp ${CORE_SOURCES})

# PostgreSQL client library
find_package(PostgreSQL REQUIRED)

# JSON library (header-only)
find_package(nlohmann_json 3.11.0 QUIET)
if(NOT nlohmann_json_FOUND)
    include(FetchContent)
    FetchContent_Declare(json 
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
        GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(json)
    set(nlohmann_json_FOUND TRUE)
endif()

# Function to link common libraries to targets (eliminates duplication)
function(link_common_libraries target_name)
    # Set include directories
    target_include_directories(${target_name} PRIVATE include)
    
    # Link PostgreSQL libraries
    target_link_libraries(${target_name} PostgreSQL::PostgreSQL)
    
    # Link JSON library
    target_link_libraries(${target_name} nlohmann_json::nlohmann_json)
    
    # Link threading library
    target_link_libraries(${target_name} Threads::Threads)
endfunction()

# Link libraries to all executables
link_common_libraries(trading_engine)
link_common_libraries(test_comprehensive)