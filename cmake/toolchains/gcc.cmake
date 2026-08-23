# =====================================================================
# MinGW GCC toolchain (x64 / x86)
#
# [To change machines, edit here - path configuration]
# Supports three install layouts, pick one:
#   A. x64/x86 under the same root (this machine: D:/cpp/toolchains/gcc has x64/, x86/)
#      -> set DESTINY_TOOLCHAIN_GCC_ROOT
#   B. x64 and x86 installed separately -> set DESTINY_TOOLCHAIN_GCC_X64_ROOT /
#      DESTINY_TOOLCHAIN_GCC_X86_ROOT (unified root can stay empty)
#   C. Only one arch installed -> set only the matching arch root
# Arch selection: passed by preset as DESTINY_TOOLCHAIN_ARCH;
# auto-detected when not passed.
# =====================================================================

# ---- Path config (edit here when changing machines) ----
set(DESTINY_TOOLCHAIN_GCC_ROOT     "D:/cpp/toolchains/gcc" CACHE STRING "GCC unified root (contains x64/, x86/); use either this or the two separate roots")
set(DESTINY_TOOLCHAIN_GCC_X64_ROOT "" CACHE STRING "GCC x64 standalone root (alternative to unified root)")
set(DESTINY_TOOLCHAIN_GCC_X86_ROOT "" CACHE STRING "GCC x86 standalone root (alternative to unified root)")
set(DESTINY_TOOLCHAIN_NINJA        "D:/cpp/ninja/ninja.exe" CACHE FILEPATH "ninja executable")
set(DESTINY_VCPKG_ROOT             "D:/cpp/vcpkg" CACHE STRING "vcpkg root")

# Ninja cannot find ninja.exe from PATH on Windows; must specify explicitly
set(CMAKE_MAKE_PROGRAM "${DESTINY_TOOLCHAIN_NINJA}" CACHE FILEPATH "ninja executable" FORCE)

# ---- Resolve bin dir for each arch (expanded directly) ----
# Prefer standalone roots; fall back to unified root subdirectory when empty
if(DESTINY_TOOLCHAIN_GCC_X64_ROOT STREQUAL "")
  set(DESTINY_GCC_X64_BIN "${DESTINY_TOOLCHAIN_GCC_ROOT}/x64/bin")
else()
  set(DESTINY_GCC_X64_BIN "${DESTINY_TOOLCHAIN_GCC_X64_ROOT}/bin")
endif()

if(DESTINY_TOOLCHAIN_GCC_X86_ROOT STREQUAL "")
  set(DESTINY_GCC_X86_BIN "${DESTINY_TOOLCHAIN_GCC_ROOT}/x86/bin")
else()
  set(DESTINY_GCC_X86_BIN "${DESTINY_TOOLCHAIN_GCC_X86_ROOT}/bin")
endif()

# ---- Available arch list (for error hints) ----
set(DESTINY_GCC_AVAILABLE "")
if(EXISTS "${DESTINY_GCC_X64_BIN}/g++.exe")
  string(APPEND DESTINY_GCC_AVAILABLE " x64")
endif()
if(EXISTS "${DESTINY_GCC_X86_BIN}/g++.exe")
  string(APPEND DESTINY_GCC_AVAILABLE " x86")
endif()

# ---- Arch selection: preset, or auto-detect when not passed ----
if(NOT DEFINED DESTINY_TOOLCHAIN_ARCH)
  if(EXISTS "${DESTINY_GCC_X64_BIN}/g++.exe")
    set(DESTINY_TOOLCHAIN_ARCH "x64")
  elseif(EXISTS "${DESTINY_GCC_X86_BIN}/g++.exe")
    set(DESTINY_TOOLCHAIN_ARCH "x86")
  endif()
endif()
if(NOT DEFINED DESTINY_TOOLCHAIN_ARCH)
  message(FATAL_ERROR "No usable GCC toolchain found. Configure the paths at the top of this file, or pass DESTINY_TOOLCHAIN_ARCH=x64/x86 in the preset")
endif()

# ---- Set compilers per selected arch (expanded branches) ----
if(DESTINY_TOOLCHAIN_ARCH STREQUAL "x86")
  if(NOT EXISTS "${DESTINY_GCC_X86_BIN}/g++.exe")
    message(FATAL_ERROR "x86 requested but compiler not found: ${DESTINY_GCC_X86_BIN}/g++.exe\nAvailable: ${DESTINY_GCC_AVAILABLE}")
  endif()
  set(CMAKE_C_COMPILER   "${DESTINY_GCC_X86_BIN}/gcc.exe")
  set(CMAKE_CXX_COMPILER "${DESTINY_GCC_X86_BIN}/g++.exe")
  set(VCPKG_TARGET_TRIPLET "x86-mingw-static")
  # x86-built executables depend on libc++.dll / libunwind.dll (llvm-mingw
  # runtime, referenced by the linker even when compiling with gcc). Copy
  # them next to the output dir (bin/) after building so they can run.
  set(DESTINY_X86_RUNTIME_DLLS
    "D:/cpp/toolchains/llvm-mingw/x86/bin/libc++.dll"
    "D:/cpp/toolchains/llvm-mingw/x86/bin/libunwind.dll")
else()
  if(NOT EXISTS "${DESTINY_GCC_X64_BIN}/g++.exe")
    message(FATAL_ERROR "x64 requested but compiler not found: ${DESTINY_GCC_X64_BIN}/g++.exe\nAvailable: ${DESTINY_GCC_AVAILABLE}")
  endif()
  set(CMAKE_C_COMPILER   "${DESTINY_GCC_X64_BIN}/gcc.exe")
  set(CMAKE_CXX_COMPILER "${DESTINY_GCC_X64_BIN}/g++.exe")
  set(VCPKG_TARGET_TRIPLET "x64-mingw-static")
endif()

# ---- vcpkg: dependencies via manifest (vcpkg.json), inline vcpkg toolchain ----
# Official support for including inside a custom toolchain, with built-in
# duplicate-load protection.
if(EXISTS "${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
  include("${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
else()
  message(WARNING "vcpkg toolchain not found: ${DESTINY_VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake; dependencies will not be managed")
endif()
