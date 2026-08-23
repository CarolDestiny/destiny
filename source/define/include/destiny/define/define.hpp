#pragma once
// destiny::define module main header: aggregates public macros and constants.
// Usage: #include "destiny/define/define.hpp"

#define DESTINY_VERSION_MAJOR 0
#define DESTINY_VERSION_MINOR 1
#define DESTINY_VERSION_PATCH 0

// Debug/Release branch: CMake BUILD_TYPE Debug defines NDEBUG
// (gcc/clang -DNDEBUG only effective in Release)
#ifndef NDEBUG
#define DESTINY_DEBUG 1
#else
#define DESTINY_DEBUG 0
#endif
