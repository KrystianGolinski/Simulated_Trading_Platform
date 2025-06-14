cmake_minimum_required(VERSION 3.16)
project(TradingEngine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

include_directories(include)

file(GLOB_RECURSE SOURCES "src/*.cpp")
file(GLOB_RECURSE HEADERS "include/*.hpp")

add_executable(trading_engine ${SOURCES} ${HEADERS})

# Database dependencies will be added later
# find_package(PkgConfig REQUIRED)
# pkg_check_modules(PQXX REQUIRED libpqxx)
# target_link_libraries(trading_engine ${PQXX_LIBRARIES})
# target_include_directories(trading_engine PRIVATE ${PQXX_INCLUDE_DIRS})
# target_compile_options(trading_engine PRIVATE ${PQXX_CFLAGS_OTHER})