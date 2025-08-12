cmake_minimum_required(VERSION 3.16)
project(cpp-common)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Create shared library
add_library(cpp-common SHARED
    src/simulation_config.cpp
    src/worker_result.cpp
)

# Set include directories
target_include_directories(cpp-common PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Install rules
install(TARGETS cpp-common
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)