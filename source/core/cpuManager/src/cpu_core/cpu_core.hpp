#pragma once

#include "destiny/define/platform/platform.hpp"

#if DESTINY_DEFINE_PLATFORM_WINDOWS == true
#include "./windows.hpp"
#endif

#if DESTINY_DEFINE_PLATFORM_LINUX == true
#include "./linux.hpp"
#endif
