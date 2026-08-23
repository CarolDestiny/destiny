#pragma once
// destiny::define 模块主头：聚合本模块公开宏与常量。
// 用法：#include "destiny/define/define.hpp"

#define DESTINY_VERSION_MAJOR 0
#define DESTINY_VERSION_MINOR 1
#define DESTINY_VERSION_PATCH 0

// 调试/发布分支：CMake 的 BUILD_TYPE Debug 会定义 NDEBUG 的相反面
// （gcc/clang 的 -DNDEBUG 仅在 Release 生效）
#ifndef NDEBUG
#define DESTINY_DEBUG 1
#else
#define DESTINY_DEBUG 0
#endif
