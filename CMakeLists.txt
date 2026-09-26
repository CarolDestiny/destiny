cmake_minimum_required(VERSION 3.25)
project(destiny_compat VERSION 0.1.0 LANGUAGES C CXX)

set(DESTINY_PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(DESTINY_SOURCE_ROOT "${DESTINY_PROJECT_ROOT}/source")
list(APPEND CMAKE_MODULE_PATH "${DESTINY_PROJECT_ROOT}/cmake")

option(DESTINY_BUILD_TESTS "Build module test programs" ON)
option(DESTINY_BUILD_BENCHMARKS "Build module benchmark programs" ON)
option(DESTINY_BUILD_DEMOS "Build module demonstration programs" ON)
option(DESTINY_NATIVE_OPTIMIZATION "Optimize project targets for this machine" ON)
set(DESTINY_RUNTIME_DIRS "" CACHE STRING "Additional explicit runtime DLL search directories")
set(DESTINY_OPTIONS_FILE "${DESTINY_PROJECT_ROOT}/cache/auto_define_config/options.json" CACHE FILEPATH "Local declared option overrides")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
enable_testing()
include(Destiny)
destiny_configure_project()
