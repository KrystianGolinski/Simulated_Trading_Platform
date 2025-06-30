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
    src/argument_parser.cpp
    src/command_dispatcher.cpp
    src/data_conversion.cpp
    src/json_helpers.cpp
    src/logger.cpp
    src/database_service.cpp
    src/execution_service.cpp
    src/progress_service.cpp
    src/result.cpp
    src/error_utils.cpp
)


# Main executable
add_executable(trading_engine src/main.cpp ${CORE_SOURCES})

# Comprehensive test executable (replaces all individual tests)
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

# Link libraries to main executable
if(nlohmann_json_FOUND)
    target_link_libraries(trading_engine ${LIBPQ_LIBRARIES} nlohmann_json::nlohmann_json)
else()
    target_link_libraries(trading_engine ${LIBPQ_LIBRARIES})
    target_include_directories(trading_engine PRIVATE ${NLOHMANN_JSON_INCLUDE_DIRS})
endif()
target_include_directories(trading_engine PRIVATE ${LIBPQ_INCLUDE_DIRS})
target_compile_options(trading_engine PRIVATE ${LIBPQ_CFLAGS_OTHER})

# Link libraries to comprehensive test executable
if(nlohmann_json_FOUND)
    target_link_libraries(test_comprehensive ${LIBPQ_LIBRARIES} nlohmann_json::nlohmann_json)
else()
    target_link_libraries(test_comprehensive ${LIBPQ_LIBRARIES})
    target_include_directories(test_comprehensive PRIVATE ${NLOHMANN_JSON_INCLUDE_DIRS})
endif()
target_include_directories(test_comprehensive PRIVATE ${LIBPQ_INCLUDE_DIRS})
target_compile_options(test_comprehensive PRIVATE ${LIBPQ_CFLAGS_OTHER})