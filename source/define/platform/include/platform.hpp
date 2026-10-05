#pragma once

#include "destiny/define/platform/_cmake.hpp"

namespace destiny::define::platform {
    static constexpr bool windows = DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS;
    static constexpr bool linux = DESTINY_CMAKE_DEFINE_PLATFORM_LINUX;
    static constexpr bool macos = DESTINY_CMAKE_DEFINE_PLATFORM_MACOS;
}

#define DESTINY_DEFINE_PLATFORM_WINDOWS DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS
#define DESTINY_DEFINE_PLATFORM_LINUX DESTINY_CMAKE_DEFINE_PLATFORM_LINUX
#define DESTINY_DEFINE_PLATFORM_MACOS DESTINY_CMAKE_DEFINE_PLATFORM_MACOS
