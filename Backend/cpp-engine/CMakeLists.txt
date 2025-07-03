cmake_minimum_required(VERSION 3.16)
project(TradingEngine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -pedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# Include directories
include_directories(include)

# Source files for main executable
set(CORE_SOURCES
    src/position.cpp
    src/portfolio.cpp
    src/order.cpp
    src/market_data.cpp
    src/trading_engine.cpp
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
)


# Main executable
add_executable(trading_engine src/main.cpp ${CORE_SOURCES})

# Test executable
add_executable(test_comprehensive tests/test_comprehensive.cpp ${CORE_SOURCES})

# Find required packages
find_package(PkgConfig REQUIRED)

# PostgreSQL client library
pkg_check_modules(LIBPQ REQUIRED libpq)

# JSON library (header-only)
find_package(nlohmann_json 3.2.0 QUIET)
if(NOT nlohmann_json_FOUND)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(NLOHMANN_JSON REQUIRED nlohmann_json)
endif()

# Function to link common libraries to targets (eliminates duplication)
function(link_common_libraries target_name)
    # Link PostgreSQL libraries
    target_link_libraries(${target_name} ${LIBPQ_LIBRARIES})
    target_include_directories(${target_name} PRIVATE ${LIBPQ_INCLUDE_DIRS})
    target_compile_options(${target_name} PRIVATE ${LIBPQ_CFLAGS_OTHER})
    
    # Link JSON library
    if(nlohmann_json_FOUND)
        target_link_libraries(${target_name} nlohmann_json::nlohmann_json)
    else()
        target_include_directories(${target_name} PRIVATE ${NLOHMANN_JSON_INCLUDE_DIRS})
    endif()
endfunction()

# Link libraries to all executables
link_common_libraries(trading_engine)
link_common_libraries(test_comprehensive)