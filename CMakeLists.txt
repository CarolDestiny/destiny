cmake_minimum_required(VERSION 3.25)

project(destiny VERSION 0.1.0 LANGUAGES CXX)

option(BUILD_SHARED_LIBS        "Build shared libs instead of static" OFF)
option(DESTINY_BUILD_TESTS      "Build unit tests (tests/)" OFF)
option(DESTINY_BUILD_EXAMPLES   "Build example programs (examples/)" OFF)
option(DESTINY_BUILD_BENCHMARKS "Build benchmark programs (benchmarks/)" ON)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
  add_compile_options(/W4)
else()
  add_compile_options(-Wall -Wextra)
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/bin")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/bin")

enable_testing()

# Export compile database (compile_commands.json) for clangd / cpptools
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(cmake/destiny_add_module.cmake)

add_subdirectory(source)