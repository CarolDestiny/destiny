# =====================================================================
# llvm-mingw Clang 工具链（x64 / x86）
#
# 【换机器时改这里 —— 路径配置】
# 支持三种安装形态，任选其一：
#   A. x64/x86 在同一根目录下（本机：D:/cpp/toolchains/llvm-mingw 下有 x64/、x86/）
#      → 设置 DESTINY_TOOLCHAIN_CLANG_ROOT
#   B. x64 与 x86 分开安装 → 分别设置 DESTINY_TOOLCHAIN_CLANG_X64_ROOT /
#      DESTINY_TOOLCHAIN_CLANG_X86_ROOT（此时统一根可留空）
#   C. 只装了其中一个架构 → 只设置对应架构根即可
# 架构选择：由 preset 传入 DESTINY_TOOLCHAIN_ARCH；未传入时自动探测可用架构。
# =====================================================================

# ---- 路径配置（换机器改这里）----
set(DESTINY_TOOLCHAIN_CLANG_ROOT     "D:/cpp/toolchains/llvm-mingw" CACHE STRING "llvm-mingw 统一根目录（含 x64/、x86/ 子目录），与两个独立根二选一")
set(DESTINY_TOOLCHAIN_CLANG_X64_ROOT "" CACHE STRING "llvm-mingw x64 独立根目录（与统一根二选一）")
set(DESTINY_TOOLCHAIN_CLANG_X86_ROOT "" CACHE STRING "llvm-mingw x86 独立根目录（与统一根二选一）")
set(DESTINY_TOOLCHAIN_NINJA          "D:/cpp/ninja/ninja.exe" CACHE FILEPATH "ninja 可执行文件")
set(DESTINY_VCPKG_ROOT               "D:/cpp/vcpkg" CACHE STRING "vcpkg 根目录")

# Ninja 生成器在 Windows 上无法从 PATH 找到 ninja.exe，必须显式指定
set(CMAKE_MAKE_PROGRAM "${DESTINY_TOOLCHAIN_NINJA}" CACHE FILEPATH "ninja 可执行文件" FORCE)

# ---- 解析两个架构各自的 bin 目录（直接展开）----
# 优先用独立根；独立根为空时回退到统一根下的子目录
if(DESTINY_TOOLCHAIN_CLANG_X64_ROOT STREQUAL "")
  set(DESTINY_CLANG_X64_BIN "${DESTINY_TOOLCHAIN_CLANG_ROOT}/x64/bin")
else()
  set(DESTINY_CLANG_X64_BIN "${DESTINY_TOOLCHAIN_CLANG_X64_ROOT}/bin")
endif()

if(DESTINY_TOOLCHAIN_CLANG_X86_ROOT STREQUAL "")
  set(DESTINY_CLANG_X86_BIN "${DESTINY_TOOLCHAIN_CLANG_ROOT}/x86/bin")
else()
  set(DESTINY_CLANG_X86_BIN "${DESTINY_TOOLCHAIN_CLANG_X86_ROOT}/bin")
endif()

# ---- 可用架构列表（供报错提示用）----
set(DESTINY_CLANG_AVAILABLE "")
if(EXISTS "${DESTINY_CLANG_X64_BIN}/clang++.exe")
  string(APPEND DESTINY_CLANG_AVAILABLE " x64")
endif()
if(EXISTS "${DESTINY_CLANG_X86_BIN}/clang++.exe")
  string(APPEND DESTINY_CLANG_AVAILABLE " x86")
endif()

# ---- 架构选择：预设传入，或未指定时自动探测 ----
if(NOT DEFINED DESTINY_TOOLCHAIN_ARCH)
  if(EXISTS "${DESTINY_CLANG_X64_BIN}/clang++.exe")
    set(DESTINY_TOOLCHAIN_ARCH "x64")
  elseif(EXISTS "${DESTINY_CLANG_X86_BIN}/clang++.exe")
    set(DESTINY_TOOLCHAIN_ARCH "x86")
  endif()
endif()
if(NOT DEFINED DESTINY_TOOLCHAIN_ARCH)
  message(FATAL_ERROR "未找到任何可用的 Clang 工具链。请配置本文件顶部的路径，或在 preset 中指定 DESTINY_TOOLCHAIN_ARCH=x64/x86")
endif()

# ---- 按所选架构设置编译器（直接展开两个分支）----
if(DESTINY_TOOLCHAIN_ARCH STREQUAL "x86")
  if(NOT EXISTS "${DESTINY_CLANG_X86_BIN}/clang++.exe")
    message(FATAL_ERROR "请求 x86 架构但未找到编译器：${DESTINY_CLANG_X86_BIN}/clang++.exe\n可用架构：${DESTINY_CLANG_AVAILABLE}")
  endif()
  set(CMAKE_C_COMPILER   "${DESTINY_CLANG_X86_BIN}/clang.exe")
  set(CMAKE_CXX_COMPILER "${DESTINY_CLANG_X86_BIN}/clang++.exe")
  set(VCPKG_TARGET_TRIPLET "x86-mingw-static")
  # x86 构建的 exe 依赖 libc++.dll / libunwind.dll（llvm-mingw 运行时），
  # 构建后复制到输出目录 bin/ 才能运行。
  set(DESTINY_X86_RUNTIME_DLLS
    "${DESTINY_CLANG_X86_BIN}/libc++.dll"
    "${DESTINY_CLANG_X86_BIN}/libunwind.dll")
else()
  if(NOT EXISTS "${DESTINY_CLANG_X64_BIN}/clang++.exe")
    message(FATAL_ERROR "请求 x64 架构但未找到编译器：${DESTINY_CLANG_X64_BIN}/clang++.exe\n可用架构：${DESTINY_CLANG_AVAILABLE}")
  endif()
  set(CMAKE_C_COMPILER   "${DESTINY_CLANG_X64_BIN}/clang.exe")
  set(CMAKE_CXX_COMPILER "${DESTINY_CLANG_X64_BIN}/clang++.exe")
  set(VCPKG_TARGET_TRIPLET "x64-mingw-static")
endif()

# ---- vcpkg：依赖统一走 manifest（vcpkg.json），内联 vcpkg toolchain ----
# 官方支持在自定义工具链内 include，自带防重复加载保护
if(EXISTS "${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
  include("${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
else()
  message(WARNING "未找到 vcpkg toolchain：${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake，依赖将不会被管理")
endif()
