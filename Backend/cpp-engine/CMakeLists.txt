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
)

set(CORE_HEADERS
    include/position.h
    include/portfolio.h
    include/order.h
    include/market_data.h
    include/trading_engine.h
)

# Main executable
add_executable(trading_engine src/main.cpp ${CORE_SOURCES} ${CORE_HEADERS})

# Test executable
add_executable(test_basic tests/test_basic.cpp ${CORE_SOURCES} ${CORE_HEADERS})

# JSON library (header-only, will be system-installed)
# target_link_libraries(trading_engine nlohmann_json::nlohmann_json)

# Database dependencies will be added in Phase 2
# find_package(PkgConfig REQUIRED)
# pkg_check_modules(PQXX REQUIRED libpqxx)
# target_link_libraries(trading_engine ${PQXX_LIBRARIES})
# target_include_directories(trading_engine PRIVATE ${PQXX_INCLUDE_DIRS})
# target_compile_options(trading_engine PRIVATE ${PQXX_CFLAGS_OTHER})