cmake_minimum_required(VERSION 3.16)
project(cpp-common)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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

# Create shared library
add_library(cpp-common SHARED
    src/simulation_config.cpp
    src/worker_result.cpp
)

# Set include directories
target_include_directories(cpp-common PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link JSON library
target_link_libraries(cpp-common nlohmann_json::nlohmann_json)

# Install rules
install(TARGETS cpp-common
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)