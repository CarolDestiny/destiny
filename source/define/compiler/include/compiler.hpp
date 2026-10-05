#pragma once

#include "destiny/define/compiler/_cmake.hpp"

namespace destiny::define::compiler {
    static constexpr bool gcc = DESTINY_CMAKE_COMPILER_GCC;
    static constexpr bool clang = DESTINY_CMAKE_COMPILER_CLANG;

    static constexpr bool x32 = DESTINY_CMAKE_COMPILER_X32;
    static constexpr bool x64 = DESTINY_CMAKE_COMPILER_X64;

    static constexpr bool debug = DESTINY_CMAKE_COMPILER_DEBUG;
    static constexpr bool release = DESTINY_CMAKE_COMPILER_RELEASE;
}

#define DESTINY_COMPILER_GCC DESTINY_CMAKE_COMPILER_GCC
#define DESTINY_COMPILER_CLANG DESTINY_CMAKE_COMPILER_CLANG

#define DESTINY_COMPILER_X32 DESTINY_CMAKE_COMPILER_X32
#define DESTINY_COMPILER_X64 DESTINY_CMAKE_COMPILER_X64

#define DESTINY_COMPILER_DEBUG DESTINY_CMAKE_COMPILER_DEBUG
#define DESTINY_COMPILER_RELEASE DESTINY_CMAKE_COMPILER_RELEASE
