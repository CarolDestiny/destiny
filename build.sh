#!/usr/bin/env bash
set -euo pipefail

# Unified build entry: default gcc-x64, optional gcc-x86 / clang-x64 / clang-x86
PRESET="${1:-gcc-x64}"

cmake --preset "$PRESET"
cmake --build --preset "$PRESET"
ctest --preset "$PRESET"
