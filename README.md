# destiny

一个模块化 C++20 项目，使用 CMake 构建，gcc/clang 双编译器 × x86/x64 四组合。

## 目录结构

```
destiny/
├── CMakeLists.txt          # 顶层构建
├── CMakePresets.json       # 构建预设（gcc/clang × x64/x86）
├── build.sh                # 统一构建入口
├── .clang-format           # 代码格式化配置
├── .gitignore
├── vcpkg.json              # 依赖清单（gtest）
├── bin/                    # 产物输出（自动生成）
├── build/                  # 构建中间目录（自动生成）
├── cache/                  # 运行期缓存
├── data/                   # 启动资源
├── docs/                   # 全局文档
├── thirdLib/               # 第三方源码
├── cmake/
│   ├── destiny_add_module.cmake   # 模块化构建引擎
│   └── toolchains/                # 编译器工具链配置
└── source/                 # 模块树根
    ├── define/             # 宏与常量（纯头）
    ├── iso/                # 系统兼容层
    ├── core/               # 核心：内存分配、日志
    ├── basicType/          # 基础类型
    ├── moreType/           # 重型类型
    └── apps/               # 应用层
```

## 构建

依赖：MinGW gcc 16.2、llvm-mingw clang 22.1、ninja、vcpkg（路径在 `cmake/toolchains/` 中配置）。

```bash
./build.sh                 # 默认 gcc-x64
./build.sh gcc-x86         # 指定预设（gcc-x64/gcc-x86/clang-x64/clang-x86）
```

## 格式化

```bash
find source -name "*.cpp" -o -name "*.hpp" | xargs clang-format -i
```

## 模块化约定

- 模块 = 目录 + `CMakeLists.txt`（内容为一行 `destiny_add_module()`）
- 目录骨架：`include/ src/ tests/ examples/ benchmarks/ docs/`
- 公开头：`include/destiny/<模块路径>/`，消费方 `#include "destiny/<模块路径>/xxx.hpp"`
- 命名空间：`destiny::<模块路径>`
