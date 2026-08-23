# destiny

A modular C++20 project built with CMake, supporting gcc/clang compilers
across x86/x64, with four build presets.

## Directory layout

```
destiny/
├── CMakeLists.txt          # top-level build
├── CMakePresets.json       # build presets (gcc/clang x x64/x86)
├── build.sh                # unified build entry
├── .clang-format           # code formatting config
├── .gitignore
├── vcpkg.json              # dependency manifest (gtest)
├── bin/                    # build output (auto-generated)
├── build/                  # CMake build dir (auto-generated)
├── cache/                  # runtime cache
├── data/                   # startup resources
├── docs/                   # global docs
├── thirdLib/               # third-party sources (vendored gtest)
├── cmake/
│   ├── destiny_add_module.cmake   # modular build engine
│   └── toolchains/                # compiler toolchain config
└── source/                 # module tree root
    ├── define/             # macros & constants (header-only)
    ├── iso/                # system compatibility layer
    ├── core/               # core: memory allocation, logging
    ├── basicType/          # basic types
    ├── moreType/           # heavy types
    └── apps/               # applications layer
```

## Build

Dependencies: MinGW gcc 16.2, llvm-mingw clang 22.1, ninja, vcpkg
(paths configured in `cmake/toolchains/`).

```bash
./build.sh                 # default gcc-x64
./build.sh gcc-x86         # choose preset (gcc-x64/gcc-x86/clang-x64/clang-x86)
```

## Formatting

```bash
find source -name "*.cpp" -o -name "*.hpp" | xargs clang-format -i
```

## Module conventions

- A module = a directory + `CMakeLists.txt` (one line: `destiny_add_module()`)
- Directory skeleton: `include/ src/ tests/ examples/ benchmarks/ docs/`
- Public headers: `include/destiny/<module path>/`, consumers write
  `#include "destiny/<module path>/xxx.hpp"`
- Namespace: `destiny::<module path>`
- Applications: `destiny_add_application()` in `source/apps/<app>/`
