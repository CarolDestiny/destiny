#!/usr/bin/env bash
set -euo pipefail

# 统一构建入口：默认 gcc-x64，可选 gcc-x86 / clang-x64 / clang-x86
PRESET="${1:-gcc-x64}"

cmake --preset "$PRESET"
cmake --build --preset "$PRESET"
ctest --preset "$PRESET"
