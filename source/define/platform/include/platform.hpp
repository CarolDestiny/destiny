#pragma once

#include "destiny/define/platform/_cmake.hpp"

namespace destiny::define::platform {
    static constexpr bool windows = DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS;
    static constexpr bool linux = DESTINY_CMAKE_DEFINE_PLATFORM_LINUX;
    static constexpr bool macos = DESTINY_CMAKE_DEFINE_PLATFORM_MACOS;
}

#define DESTINY_DEFINE_PLATFORM_WINDOWS ::destiny::define::platform::windows
#define DESTINY_DEFINE_PLATFORM_LINUX ::destiny::define::platform::linux
#define DESTINY_DEFINE_PLATFORM_MACOS ::destiny::define::platform::macos
