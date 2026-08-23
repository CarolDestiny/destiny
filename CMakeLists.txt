cmake_minimum_required(VERSION 3.25)

project(destiny VERSION 0.1.0 LANGUAGES CXX)

option(BUILD_SHARED_LIBS        "构建共享库而非静态库" OFF)
option(DESTINY_BUILD_TESTS      "构建单元测试 (tests/)" ON)
option(DESTINY_BUILD_EXAMPLES   "构建样例程序 (examples/)" OFF)
option(DESTINY_BUILD_BENCHMARKS "构建跑分程序 (benchmarks/)" OFF)

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

# 导出编译数据库（compile_commands.json）供 clangd / cpptools 使用
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(cmake/destiny_add_module.cmake)

add_subdirectory(source)