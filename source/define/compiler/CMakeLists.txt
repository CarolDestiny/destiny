if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    set(DESTINY_CMAKE_COMPILER_GCC true)
    set(DESTINY_CMAKE_COMPILER_CLANG false)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(DESTINY_CMAKE_COMPILER_GCC false)
    set(DESTINY_CMAKE_COMPILER_CLANG true)
else()
    set(DESTINY_CMAKE_COMPILER_GCC false)
    set(DESTINY_CMAKE_COMPILER_CLANG false)
endif()

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(DESTINY_CMAKE_COMPILER_X32 false)
    set(DESTINY_CMAKE_COMPILER_X64 true)
elseif(CMAKE_SIZEOF_VOID_P EQUAL 4)
    set(DESTINY_CMAKE_COMPILER_X32 true)
    set(DESTINY_CMAKE_COMPILER_X64 false)
else()
    set(DESTINY_CMAKE_COMPILER_X32 false)
    set(DESTINY_CMAKE_COMPILER_X64 false)
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(DESTINY_CMAKE_COMPILER_DEBUG true)
    set(DESTINY_CMAKE_COMPILER_RELEASE false)
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(DESTINY_CMAKE_COMPILER_DEBUG false)
    set(DESTINY_CMAKE_COMPILER_RELEASE true)
else()
    set(DESTINY_CMAKE_COMPILER_DEBUG false)
    set(DESTINY_CMAKE_COMPILER_RELEASE true)
endif()

configure_file(
        "${CMAKE_CURRENT_LIST_DIR}/include/_cmake.hpp.in"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/compiler/_cmake.hpp"
        @ONLY
)

add_library(destiny_define_compiler INTERFACE)

target_include_directories(
        destiny_define_compiler
        INTERFACE
        $<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>
)

file(MAKE_DIRECTORY "${DESTINY_INCLUDE_ROOT}/destiny/define/compiler")

file(
        CREATE_LINK
        "${CMAKE_CURRENT_SOURCE_DIR}/include/compiler.hpp"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/compiler/compiler.hpp"
        SYMBOLIC
)
